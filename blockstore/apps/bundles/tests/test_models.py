"""
Test Bundle Models
"""
import uuid

from django.core.files.base import ContentFile
from django.test import TestCase

from ..store import BundleDataStore
from ..models import Bundle
from .factories import CollectionFactory


class TestBundleVersionCreation(TestCase):
    """ Tests for BundleVersion model. """

    def setUp(self):

        super().setUp()

        self.collection = CollectionFactory(title="Collection 1")

    def test_auto_creation(self):
        """Creating a Snapshot should trigger creation of a BundleVersion."""
        bundle_uuid = uuid.UUID('10000000000000000000000000000000')

        # First make sure the Bundles doesn't already exist.
        self.assertRaises(Bundle.DoesNotExist, Bundle.objects.get, uuid=bundle_uuid)

        # Create our BundleSnapshot
        store = BundleDataStore()
        file_mapping = {
            'hello.txt': ContentFile(b"Hello World!"),
        }

        # Bundle doesn't exist yet, so creating a snapshot should fail.
        with self.assertRaises(Bundle.DoesNotExist):
            store.create_snapshot(bundle_uuid, file_mapping)

        # Bundle creation and the first version
        bundle = Bundle.objects.create(
            uuid=bundle_uuid, title="Auto-Create Test Bundle", collection=self.collection
        )
        snapshot_1 = store.create_snapshot(bundle_uuid, file_mapping)
        self.assertEqual(bundle.versions.count(), 1)
        version_1 = bundle.versions.get(version_num=1)
        self.assertEqual(version_1.snapshot_digest, snapshot_1.hash_digest)

        # Second snapshot
        file_mapping = {
            'aloha.txt': ContentFile(b"Aloha a hui hou!")
        }
        snapshot_2 = store.create_snapshot(bundle_uuid, file_mapping)
        self.assertEqual(bundle.versions.count(), 2)
        version_2 = bundle.versions.get(version_num=2)
        self.assertEqual(version_2.snapshot_digest, snapshot_2.hash_digest)
        self.assertNotEqual(snapshot_1, snapshot_2)

        # Third version is going to point to the first snapshot (simulate a revert).
        version_3 = bundle.versions.create(
            version_num=3, snapshot_digest=snapshot_1.hash_digest
        )
        self.assertEqual(snapshot_1, version_3.snapshot())
