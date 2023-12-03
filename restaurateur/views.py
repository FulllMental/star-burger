from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Product, Restaurant, OrderDetails, RestaurantMenuItem
from foodcartapp.views import add_new_place
from geocoder.models import Places


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


def client_coordinates_change_check(order, all_places_coords):
    try:
        client_coordinates = all_places_coords[order.address]
    except KeyError:
        add_new_place(order.address)
        client_place = Places.objects.get(address=order.address)
        client_coordinates = (client_place.lat, client_place.lon)
    return client_coordinates


def get_ready_restaurants(order, working_restaurants, available_menu_items):
    if order.chosen_restaurant:
        return order.chosen_restaurant, []
    capable_restaurants = working_restaurants.copy()
    products = order.ordered_products.all()
    for product in products:
        incapable_restaurants = available_menu_items.filter(product=product.product, availability=False)
    for incapable_restaurant in incapable_restaurants:
        capable_restaurants.pop(incapable_restaurant.restaurant.address)
    return [], capable_restaurants


def get_restaurants_to_choose(client_coordinates, all_places_coords, available_restaurants):
    restaurants_to_choose = {}
    for capable_restaurant in available_restaurants:
        restaurant_coordinates = all_places_coords[capable_restaurant.lower()]
        if not (restaurant_coordinates or client_coordinates):
            restaurants_to_choose[available_restaurants[capable_restaurant]] = 'Ошибка определения координат'
        else:
            distance_to_client = distance.distance(restaurant_coordinates, client_coordinates).km
            restaurants_to_choose[available_restaurants[capable_restaurant]] = f'{round(distance_to_client, 2)}км.'
    return sorted(restaurants_to_choose.items(), key=lambda x: x[1])


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = OrderDetails.objects.with_price().prefetch_related('ordered_products')
    places = Places.objects.all()
    all_places_coords = {place.address: (place.lat, place.lon) for place in places}
    available_menu_items = RestaurantMenuItem.objects.select_related('restaurant').select_related('product')
    working_restaurants = {position.restaurant.address: position.restaurant.name for position in available_menu_items}
    redirect_url = request.get_full_path()
    order_items = []
    for order in orders:
        client_coordinates = client_coordinates_change_check(order, all_places_coords)
        chosen_restaurant, available_restaurants = get_ready_restaurants(order, working_restaurants, available_menu_items)
        restaurants_to_choose = get_restaurants_to_choose(client_coordinates, all_places_coords, available_restaurants)
        if restaurants_to_choose:
            restaurants_to_choose = [f'{restaurant[0]} - {restaurant[1]}' for restaurant in restaurants_to_choose]
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
            'capable_restaurants': restaurants_to_choose,
        })
    return render(request, template_name='order_items.html', context={"order_items": order_items,
                                                                      'redirect_url': redirect_url})
