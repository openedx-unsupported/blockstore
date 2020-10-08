""" Command to create a bundle. """

import pathlib


from django.core.management.base import BaseCommand

from ...models import Bundle, Collection
from ...store import SnapshotRepo, files_from_disk


class Command(BaseCommand):
    """ Command to create a bundle. """

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
        bundle = Bundle.objects.create(
            slug=slug, title=title, description=description, collection=Collection.objects.first()
        )
        print(f"Created Bundle: {bundle.uuid} ({bundle.title})")

        # Fetch Bundle data from source directory
        bundle_data_path = pathlib.Path(bundle_src)
        store = SnapshotRepo()

        with files_from_disk(bundle_data_path) as bundle_version_files:
            store.create(bundle.uuid, bundle_version_files)
