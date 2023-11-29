import os

import requests
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.conf import settings
from dotenv import load_dotenv
from geopy import distance

from foodcartapp.models import Product, Restaurant, OrderDetails, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )
    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def get_restaurants_distance(order, working_restaurants, available_positions):
    if order.chosen_restaurant:
        return order.chosen_restaurant, []
    apikey = settings.GEOPY_API_KEY
    restaurants_to_choose = {}
    client_address = order.address
    client_coordinates = fetch_coordinates(apikey, client_address)
    capable_restaurants = working_restaurants.copy()
    products = order.ordered_products.all()
    for product in products:
        incapable_restaurants = available_positions.filter(product=product.product, availability=False)
    for incapable_restaurant in incapable_restaurants:
        capable_restaurants.pop(incapable_restaurant.restaurant.address)
    for capable_restaurant in capable_restaurants:
        restaurant_coordinates = fetch_coordinates(apikey, capable_restaurant)
        if not (restaurant_coordinates or client_coordinates):
            restaurants_to_choose[capable_restaurants[capable_restaurant]] = 'Ошибка определения координат'
        else:
            distance_to_client = distance.distance(restaurant_coordinates, client_coordinates).km
            restaurants_to_choose[capable_restaurants[capable_restaurant]] = f'{round(distance_to_client, 2)}км.'
    return [], sorted(restaurants_to_choose.items(), key=lambda x: x[1])


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = OrderDetails.objects.with_price().prefetch_related('ordered_products')
    available_positions = RestaurantMenuItem.objects.select_related('restaurant').select_related('product')
    working_restaurants = {position.restaurant.address: position.restaurant.name for position in available_positions}

    redirect_url = request.get_full_path()
    order_items = []

    for order in orders:
        chosen_restaurant, available_restaurants = get_restaurants_distance(order,
                                                                            working_restaurants,
                                                                            available_positions)
        if available_restaurants:
            available_restaurants = [f'{available_restaurant[0]} - {available_restaurant[1]}' for
                                     available_restaurant in available_restaurants]
        order_items.append({
            'id': order.id,
            'total_price': order.total_price,
            'get_payment_method_display': order.get_payment_method_display,
            'get_status_display': order.get_status_display,
            'name': f'{order.firstname} {order.lastname}',
            'phonenumber': order.phonenumber,
            'address': order.address,
            'comment': order.comment,
            'chosen_restaurant': chosen_restaurant,
            'capable_restaurants': available_restaurants,
        })
    return render(request, template_name='order_items.html', context={"order_items": order_items, 'redirect_url': redirect_url})
