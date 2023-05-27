from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from phonenumbers import parse, is_valid_number

from .models import Product, OrderDetails, OrderedProducts
import json


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


def validate_order(new_order):
    order_keys = ['firstname', 'lastname', 'address']
    for order_key in order_keys:
        if not new_order.get(order_key):
            content = {'error': f'похоже что {order_key} отсутствует или указано значение None/Null/0/False...'}
            return content, False
        if not isinstance(new_order[order_key], str):
            content = {'error': f'получен неподдерживаемый формат данных в параметре "{order_key}"...'}
            return content, False

    if not new_order.get('phonenumber'):
        content = {'error': '"phonenumber" отсутствует...'}
        return content, False
    client_phonenumber = parse(new_order['phonenumber'], 'RU')
    if not is_valid_number(client_phonenumber):
        content = {'error': '"phonenumber" не подходит под формат региона...'}
        return content, False

    if not new_order.get('products'):
        content = {'error': 'похоже что список "products" отсутствует или оказался пустым...'}
        return content, False
    ordered_products = new_order['products']
    if not isinstance(ordered_products, list):
        content = {'error': 'похоже вместо списка "products" получен другой формат данных...'}
        return content, False

    all_ordered_products = [ordered_product['product'] for ordered_product in ordered_products]
    all_products = Product.objects.all()
    last_product_id = list(all_products)[-1].id
    for product_id in all_ordered_products:
        if not 0 < int(product_id) <= last_product_id:
            content = {'error': f'Позиции с индексом {product_id} не существует...'}
            return content, False
    return {}, True


@api_view(['POST'])
def register_order(request):
    new_order = request.data
    content, validation = validate_order(new_order)
    if not validation:
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    defaults = {
        'lastname': new_order.get('lastname', ''),
    }

    order = OrderDetails.objects.get_or_create(firstname=new_order['firstname'],
                                               phonenumber=new_order['phonenumber'],
                                               address=new_order['address'],
                                               defaults=defaults)
    products = Product.objects.all()
    for product in new_order['products']:
        OrderedProducts.objects.create(product=products[product['product']-1],
                                       quantity=product['quantity'],
                                       order=order[0])
    return Response(order[1])
