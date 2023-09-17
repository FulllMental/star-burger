from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Product, OrderDetails, OrderedProducts, RestaurantMenuItem


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


def get_all_restaurants(available_positions):
    all_restaurants_position = available_positions.values_list('restaurant__name')
    all_working_restaurants = set()
    for restaurant_position in all_restaurants_position:
        if restaurant_position[0] in all_restaurants_position:
            continue
        all_working_restaurants.add(f'<li>{restaurant_position[0]}</li>')
    return all_working_restaurants


def remove_incapable_restaurants(available_positions, all_possible_restaurants, product):
    incapable_restaurants = available_positions.filter(product=list(product.items())[0][1], availability=False)
    for incapable_restaurant in incapable_restaurants:
        restaurant_to_remove = incapable_restaurant.restaurant.name
        if restaurant_to_remove not in all_possible_restaurants:
            continue
        all_possible_restaurants.remove(restaurant_to_remove)


@transaction.atomic()
@api_view(['POST'])
def register_order(request):
    serializer = OrderDetailsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order = OrderDetails.objects.create(firstname=serializer.validated_data['firstname'],
                                        lastname=serializer.validated_data['lastname'],
                                        phonenumber=serializer.validated_data['phonenumber'],
                                        address=serializer.validated_data['address'])

    available_positions = RestaurantMenuItem.objects.select_related('restaurant').select_related('product')
    all_restaurants = get_all_restaurants(available_positions)

    for product in serializer.validated_data['products']:
        remove_incapable_restaurants(available_positions, all_restaurants, product)
        OrderedProducts.objects.create(product=product['product'],
                                       quantity=product['quantity'],
                                       order=order,
                                       fixed_price=product['product'].price)
    if not all_restaurants:
        capable_restaurants = 'Подходящих ресторанов не найдено'
    else:
        capable_restaurants = ''.join(all_restaurants)
    order.capable_restaurants = capable_restaurants
    order.save()
    return Response(OrderDetailsSerializer(order).data)
