# Generated by Django 3.2.15 on 2023-08-09 19:41

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_orderdetails_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetails',
            name='called_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='время созвона'),
        ),
        migrations.AddField(
            model_name='orderdetails',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='время доставки'),
        ),
        migrations.AddField(
            model_name='orderdetails',
            name='register_time',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 9, 19, 41, 24, 473737, tzinfo=utc), verbose_name='время заказа'),
        ),
    ]
