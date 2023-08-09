from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderDetailsQuerySet(models.QuerySet):
    def with_price(self):
        price = Sum(F('ordered_products__fixed_price') * F('ordered_products__quantity'))
        return self.annotate(total_price=price)


class OrderDetails(models.Model):
    order_status_choices = [
        ('1', 'Не обработан'),
        ('2', 'Не собран'),
        ('3', 'Не доставлен'),
        ('4', 'Доставлен'),
    ]
    payment_method_choices = [
        ('CS', 'Наличностью'),
        ('EL', 'Электронно'),
    ]
    firstname = models.CharField(verbose_name='имя',
                                 max_length=150)
    lastname = models.CharField(verbose_name='фамилия',
                                null=True,
                                max_length=150,)
    phonenumber = PhoneNumberField(region="RU",
                                   verbose_name='Номер телефона',)
    address = models.CharField(verbose_name='адрес',
                               max_length=150,)
    objects = OrderDetailsQuerySet.as_manager()
    status = models.CharField(verbose_name='статус заказа',
                              max_length=2,
                              choices=order_status_choices,
                              default='1',
                              db_index=True,
                              )
    payment_method = models.CharField(verbose_name='метод оплаты',
                              max_length=2,
                              choices=payment_method_choices,
                              default='CS',
                              db_index=True,
                              )
    comment = models.TextField(
        verbose_name='комментарий к заказу',
        null=True,
        blank=True,
        default=''
    )
    register_time = models.DateTimeField(verbose_name='время заказа',
                                         default=timezone.now())
    called_at = models.DateTimeField(verbose_name='время созвона',
                                     null=True,
                                     blank=True)
    delivered_at = models.DateTimeField(verbose_name='время доставки',
                                        null=True,
                                        blank=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        unique_together = [
            ['firstname', 'address']
        ]

    def __str__(self):
        return f"{self.firstname} - {self.address}"


class OrderedProducts(models.Model):
    product = models.ForeignKey('Product',
                                on_delete=models.CASCADE,
                                related_name='ordered_products',
                                verbose_name='продукт',)
    quantity = models.IntegerField(verbose_name='количество')
    order = models.ForeignKey('OrderDetails',
                              on_delete=models.CASCADE,
                              related_name='ordered_products',
                              verbose_name='заказ',)
    fixed_price = models.DecimalField(decimal_places=2,
                                      max_digits=5,
                                      validators=[MinValueValidator(0, 0)])

    class Meta:
        verbose_name = 'позиция в заказе'
        verbose_name_plural = 'позиции в заказах'

    def __str__(self):
        return f"{self.product.name} - {self.order.firstname} - {self.order.address}"
