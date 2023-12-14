from django.db import models


class Places(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True
    )
    lat = models.FloatField(verbose_name='Координаты: широта',
                            null=True)
    lon = models.FloatField(verbose_name='Координаты: долгота',
                            null=True)
    request_datetime = models.DateTimeField(verbose_name='Дата запроса к API geopy')
