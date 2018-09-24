"""
Test BundleStore functionality (where we actually persist Bundle file data).
"""
from unittest import mock, TestCase
import hashlib
import uuid

from django.core.files.base import ContentFile

from ..store import BundleDataStore, FileInfo


HTML_CONTENT_BYTES = b"<p>I am an HTML file!</p>"
TEXT_CONTENT_BYTES = b"I am a text file!"

HTML_FILE = ContentFile(HTML_CONTENT_BYTES)
TEXT_FILE = ContentFile(TEXT_CONTENT_BYTES)


@mock.patch('blockstore.apps.bundles.store.snapshot_created.send')
class TestBundleSnapshots(TestCase):
    """
    Test basic snapshot creation and querying.

    We inherit from unittest.TestCase here at the moment because we don't need
    the ability to reset the Django database. We suppress the only side-effect
    Django Signal that BundleSnapshots emit, and the in-memory File Storage
    configured for tests isn't set to persist anything across storage
    references. If any of these assumptions change, tests here will likely start
    breaking.
    """
    def test_basic_creation(self, snapshot_created_mock):
        BUNDLE_UUID = uuid.UUID('12345678123456781234567812345678')
        store = BundleDataStore()
        file_mapping = {
            'test.html': HTML_FILE,
            'test.txt': TEXT_FILE,
        }
        snapshot = store.create_snapshot(BUNDLE_UUID, file_mapping)
        self.assertEqual(snapshot.bundle_uuid, BUNDLE_UUID)
        self.assertEqual(
            snapshot.files,
            {
                'test.html': FileInfo(
                    path='test.html',
                    public=False,
                    size=25,
                    hash_digest=hashlib.blake2b(  # pylint: disable=no-member
                        HTML_CONTENT_BYTES, digest_size=20
                    ).digest(),
                ),
                'test.txt': FileInfo(
                    path='test.txt',
                    public=False,
                    size=17,
                    hash_digest=hashlib.blake2b(  # pylint: disable=no-member
                        TEXT_CONTENT_BYTES, digest_size=20
                    ).digest(),
                ),
            }
        )

        # Test our Django Signal for external notification
        snapshot_created_mock.assert_called_with(
            BundleDataStore,
            bundle_uuid=BUNDLE_UUID,
            hash_digest=mock.ANY,
        )

        # Make sure we can pull the BundleSnapshot back out of the BundleStore
        # (i.e. it was actually persisted).
        self.assertEqual(snapshot, store.snapshot(BUNDLE_UUID, snapshot.hash_digest))

    def test_multiple_snapshots(self, snapshot_created_mock):
        BUNDLE_UUID = uuid.UUID('02345678123456781234567812345678')
        store = BundleDataStore()
        snapshot_1 = store.create_snapshot(BUNDLE_UUID, {'test.txt': TEXT_FILE})
        print(snapshot_created_mock.call_args)
        self.assertEqual(
            snapshot_created_mock.call_args[1]['hash_digest'],
            snapshot_1.hash_digest
        )
        snapshot_2 = store.create_snapshot(BUNDLE_UUID, {'renamed.txt': TEXT_FILE})
        self.assertEqual(
            snapshot_created_mock.call_args[1]['hash_digest'],
            snapshot_2.hash_digest
        )

        self.assertEqual(snapshot_1.bundle_uuid, snapshot_2.bundle_uuid)
        self.assertNotEqual(snapshot_1, snapshot_2)
        self.assertNotEqual(snapshot_1.hash_digest, snapshot_2.hash_digest)
        self.assertEqual(
            snapshot_1.files['test.txt'].hash_digest,  # pylint: disable=unsubscriptable-object
            snapshot_2.files['renamed.txt'].hash_digest,  # pylint: disable=unsubscriptable-object
        )
