import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from foodcartapp.models import Restaurant
from foodcartapp.views import add_new_place
from geocoder.models import Places


class Command(BaseCommand):
    help = 'Автозагрузчик данных о ресторанах | restaurants data autoloader'

    def handle(self, *args, **options):
        restaurants = Restaurant.objects.all()
        places = Places.objects.all()
        for restaurant in restaurants:
            address = restaurant.address.lower()
            try:
                places.get(address=address)
            except ObjectDoesNotExist:
                logging.warning(f"Couldn't find place {address}, creating new...")
                add_new_place(address=address)

