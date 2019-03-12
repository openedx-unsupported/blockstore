""" Command to create a bundle version. """

import pathlib
import uuid

from django.core.management.base import BaseCommand

from ...store import SnapshotRepo, files_from_disk


class Command(BaseCommand):
    """ Command to create a bundle version. """

    help = 'Creates a Bundle Version'

    def add_arguments(self, parser):
        parser.add_argument('bundle_uuid')
        parser.add_argument('bundle_src')

    def handle(self, *args, **options):
        bundle_uuid = uuid.UUID(options['bundle_uuid'])
        bundle_src = options['bundle_src']

        # Fetch Bundle data from source directory
        bundle_data_path = pathlib.Path(bundle_src)

        # Now call the SnapshotRepo
        store = SnapshotRepo()
        with files_from_disk(bundle_data_path) as bundle_version_files:
            store.create(bundle_uuid, bundle_version_files)
