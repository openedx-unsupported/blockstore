import os
import os.path
import pathlib
import uuid

from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from ...models import Bundle
from ...store import BundleDataStore, files_from_disk


class Command(BaseCommand):
    help = 'Creates a Bundle Version'

    def add_arguments(self, parser):
        parser.add_argument('bundle_uuid')
        parser.add_argument('bundle_src')

    def handle(self, *args, **options):
        bundle_uuid = uuid.UUID(options['bundle_uuid'])
        bundle_src = options['bundle_src']

        # Fetch Bundle data from source directory
        bundle_data_path = pathlib.Path(bundle_src)

        # Now call the BundleDataStore
        store = BundleDataStore()
        with files_from_disk(bundle_data_path) as bundle_version_files:
            store.create_snapshot(bundle_uuid, bundle_version_files)



