# Generated by Django 3.2.15 on 2023-12-02 15:32

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_auto_20230917_2242'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderdetails',
            name='capable_restaurants',
        ),
        migrations.AlterField(
            model_name='orderdetails',
            name='register_time',
            field=models.DateTimeField(default=datetime.datetime(2023, 12, 2, 15, 32, 55, 479088, tzinfo=utc), verbose_name='время заказа'),
        ),
    ]
