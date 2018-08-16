from django.core.management.base import BaseCommand, CommandError

from ...models import Collection

class Command(BaseCommand):
    help = 'Creates a Collection'

    def add_arguments(self, parser):
        parser.add_argument('title', action='store')

    def handle(self, *args, **options):
        title = options['title']
        collection = Collection.objects.create(title=title)
        print("Created Collection: {} ({})".format(collection.uuid, collection.title))

