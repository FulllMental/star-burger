# Generated by Django 3.2.15 on 2023-08-09 19:44

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20230809_2241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdetails',
            name='register_time',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 9, 19, 44, 21, 124604, tzinfo=utc), verbose_name='время заказа'),
        ),
    ]
