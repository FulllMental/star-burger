from rest_framework.serializers import ModelSerializer
from .models import OrderDetails, OrderedProducts


class OrderedProductsSerializer(ModelSerializer):
    class Meta:
        model = OrderedProducts
        fields = ['product', 'quantity']

    def create(self, validated_data, order):
        OrderedProducts.objects.create(product=validated_data['product'],
                                       quantity=validated_data['quantity'],
                                       order=order,
                                       fixed_price=validated_data['product'].price)


class OrderDetailsSerializer(ModelSerializer):
    products = OrderedProductsSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = OrderDetails
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']

    def create(self, validated_data):
        order = OrderDetails.objects.create(firstname=validated_data['firstname'],
                                        lastname=validated_data['lastname'],
                                        phonenumber=validated_data['phonenumber'],
                                        address=validated_data['address'].lower())
        return order
