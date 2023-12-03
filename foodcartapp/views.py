from datetime import datetime

import requests
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from geocoder.models import Places
from .models import Product, OrderDetails, OrderedProducts


class OrderedProductsSerializer(ModelSerializer):
    class Meta:
        model = OrderedProducts
        fields = ['product', 'quantity']


class OrderDetailsSerializer(ModelSerializer):
    products = OrderedProductsSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = OrderDetails
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
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


def add_new_place(address):
    apikey = settings.GEOPY_API_KEY
    lat, lon = fetch_coordinates(apikey, address)
    request_datetime = datetime.now()
    Places.objects.create(address=address,
                          lat=lat,
                          lon=lon,
                          request_datetime=request_datetime)


@transaction.atomic()
@api_view(['POST'])
def register_order(request):
    serializer = OrderDetailsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    address = serializer.validated_data['address'].lower()
    place_record = Places.objects.filter(address=address)
    if not place_record:
        add_new_place(address)

    order = OrderDetails.objects.create(firstname=serializer.validated_data['firstname'],
                                        lastname=serializer.validated_data['lastname'],
                                        phonenumber=serializer.validated_data['phonenumber'],
                                        address=address)

    for product in serializer.validated_data['products']:
        OrderedProducts.objects.create(product=product['product'],
                                       quantity=product['quantity'],
                                       order=order,
                                       fixed_price=product['product'].price)
    return Response(OrderDetailsSerializer(order).data)
