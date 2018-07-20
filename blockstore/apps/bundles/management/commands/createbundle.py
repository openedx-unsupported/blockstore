import os
import os.path
import pathlib

from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from ...models import Bundle
from ...store import BundleDataStore, files_from_disk


class Command(BaseCommand):
    help = 'Creates a Bundle'

    def add_arguments(self, parser):
        parser.add_argument('bundle_src')
        parser.add_argument('--slug', default='test_bundle')
        parser.add_argument('--title', default='Bundle Test Title')
        parser.add_argument('--description', default='Test Description')

    def handle(self, *args, **options):
        bundle_src = options['bundle_src']
        slug = options['slug']
        title = options['title']
        description = options['description']

        # Create Bundle -- there are no Versions at this point.
        bundle = Bundle.objects.create(slug=slug, title=title, description=description)
        print("Created Bundle: {} ({})".format(bundle.uuid, bundle.title))

        # Fetch Bundle data from source directory
        bundle_data_path = pathlib.Path(bundle_src)
        store = BundleDataStore()

        with files_from_disk(bundle_data_path) as bundle_version_files:
            store.create_snapshot(bundle.uuid, bundle_version_files)



