""" Command to create a collection. """

from django.core.management.base import BaseCommand

from ...models import Collection


class Command(BaseCommand):
    """ Command to create a collection. """

    help = 'Creates a Collection'

    def add_arguments(self, parser):
        parser.add_argument('title', action='store')

    def handle(self, *args, **options):
        title = options['title']
        collection = Collection.objects.create(title=title)
        print(f"Created Collection: {collection.uuid} ({collection.title})")
