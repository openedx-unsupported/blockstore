"""
Test Bundle Models
"""
import uuid

from django.core.files.base import ContentFile
from django.test import TestCase

from blockstore.apps.bundles.tests.storage_utils import isolate_test_storage
from ..store import SnapshotRepo
from ..models import Bundle, Collection, Draft
from .factories import CollectionFactory, BundleFactory


@isolate_test_storage
class TestBundleVersionCreation(TestCase):
    """ Tests for BundleVersion model. """

    def setUp(self):
        super().setUp()
        self.collection = CollectionFactory(title="Collection 1")

    def test_create_and_rollback(self):
        """Snapshot + BundleVersion creation and rollback."""
        bundle_uuid = uuid.UUID('10000000000000000000000000000000')

        # First make sure the Bundles doesn't already exist.
        self.assertRaises(Bundle.DoesNotExist, Bundle.objects.get, uuid=bundle_uuid)

        # Create our Snapshot
        store = SnapshotRepo()
        file_mapping = {
            'hello.txt': ContentFile(b"Hello World!"),
        }

        # Bundle creation
        bundle = Bundle.objects.create(
            uuid=bundle_uuid, title="Auto-Create Test Bundle", collection=self.collection
        )
        self.assertIsNone(bundle.get_bundle_version())

        # Create the first snapshot
        snapshot_1 = store.create(bundle_uuid, file_mapping)
        bundle.new_version_from_snapshot(snapshot_1)
        self.assertEqual(bundle.versions.count(), 1)
        version_1 = bundle.versions.get(version_num=1)
        self.assertEqual(version_1.snapshot_digest, snapshot_1.hash_digest.hex())

        # Version 1 is the latest version
        self.assertEqual(bundle.get_bundle_version(), version_1)

        # Second snapshot
        file_mapping = {
            'aloha.txt': ContentFile(b"Aloha a hui hou!")
        }
        snapshot_2 = store.create(bundle_uuid, file_mapping)
        bundle.new_version_from_snapshot(snapshot_2)
        self.assertEqual(bundle.versions.count(), 2)
        version_2 = bundle.versions.get(version_num=2)
        self.assertEqual(version_2.snapshot_digest, snapshot_2.hash_digest.hex())
        self.assertNotEqual(snapshot_1, snapshot_2)

        # Version 2 should now be the latest version, and we can still access the others.
        self.assertEqual(bundle.get_bundle_version(), version_2)
        self.assertEqual(bundle.get_bundle_version(1), version_1)
        self.assertEqual(bundle.get_bundle_version(2), version_2)
        self.assertIsNone(bundle.get_bundle_version(3))

        # Third version is going to point to the first snapshot (simulate a revert).
        version_3 = bundle.new_version_from_snapshot(snapshot_1)
        self.assertEqual(snapshot_1, version_3.snapshot())

        # Version 3 is now the latest version
        self.assertEqual(bundle.get_bundle_version(), version_3)


@isolate_test_storage
class TestToString(TestCase):
    """
    Tests the string representations of the models.
    """
    def setUp(self):
        super().setUp()

        self.uuid1 = uuid.UUID('10000000000000000000000000000000')
        self.uuid2 = uuid.UUID('20000000000000000000000000000000')
        self.collection = CollectionFactory(uuid=self.uuid1, title="Collection 1")
        self.bundle = BundleFactory(uuid=self.uuid2, collection=self.collection, slug="bundle-1")

        store = SnapshotRepo()
        file_mapping = {
            'hello.txt': ContentFile(b"Hello World!"),
        }
        self.snapshot = store.create(self.uuid2, file_mapping)
        self.bundle.new_version_from_snapshot(self.snapshot)
        self.version = self.bundle.versions.get(version_num=1)

    def test_collection_str(self):
        self.assertEqual(str(self.collection), " - ".join([str(self.uuid1), "Collection 1"]))

    def test_bundle_str(self):
        self.assertEqual(str(self.bundle), "Bundle {} - {}".format(self.uuid2, "bundle-1"))

    def test_version_str(self):
        self.assertEqual(str(self.version), "{}@{}".format(self.uuid2, 1))


@isolate_test_storage
class TestDraftCreation(TestCase):
    """
    Test creation of a new draft
    """
    def test_save_creates_staged_draft(self):
        collection = Collection.objects.create(title="Collection 1")
        bundle = Bundle.objects.create(
            uuid=uuid.UUID('10000000000000000000000000000000'),
            collection=collection,
            title="Test Bundle for Draft Testing",
        )
        draft = Draft.objects.create(name="demo_draft", bundle=bundle)
        self.assertEqual(draft.bundle_uuid, bundle.uuid)
        staged_draft = draft.staged_draft
        self.assertEqual(staged_draft.files_to_overwrite, {})
        self.assertIsNone(staged_draft.base_snapshot)
