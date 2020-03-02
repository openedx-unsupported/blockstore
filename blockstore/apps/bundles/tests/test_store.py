"""
Test BundleStore functionality (where we actually persist Bundle file data).
"""
from unittest import mock
import unittest
import codecs
import uuid

from django.test import SimpleTestCase
from django.core.files.base import ContentFile

from blockstore.apps.bundles.tests.storage_utils import isolate_test_storage
from ..store import (
    create_hash,
    DraftRepo,
    Dependency,
    FileInfo,
    Link,
    LinkCollection,
    Snapshot,
    SnapshotRepo,
    StagedDraft,
)


HTML_CONTENT_BYTES = b"<p>I am an HTML file!</p>"
TEXT_CONTENT_BYTES = b"I am a text file!"

HTML_FILE = ContentFile(HTML_CONTENT_BYTES)
TEXT_FILE = ContentFile(TEXT_CONTENT_BYTES)


class TestFileInfo(unittest.TestCase):
    """
    Basic tests of the FileInfo structure
    """
    def test_serialization(self):
        """
        Test creation from Python primitives (that you'd get from JSON parsing).
        """
        sample_data = {
            "a/file-1.html": [False, 25, "c0c0940e4b3151908b60cecd1ef5e2aa19904676"],
            "b/file-2.txt": None
        }
        file_info = FileInfo.from_json_dict(sample_data)

        self.assertEqual(
            file_info,
            {
                "a/file-1.html": FileInfo(
                    path="a/file-1.html",
                    public=False,
                    size=25,
                    hash_digest=codecs.decode("c0c0940e4b3151908b60cecd1ef5e2aa19904676", 'hex')
                ),
                "b/file-2.txt": None
            }
        )


@isolate_test_storage
class TestSnapshots(SimpleTestCase):
    """
    Test basic snapshot creation and querying.

    We inherit from unittest.TestCase here at the moment because we don't need
    the ability to reset the Django database. We suppress the only side-effect
    Django Signal that Snapshots emit, and the in-memory File Storage
    configured for tests isn't set to persist anything across storage
    references. If any of these assumptions change, tests here will likely start
    breaking.
    """
    @mock.patch('blockstore.apps.bundles.store.snapshot_created.send')
    def test_basic_creation(self, snapshot_created_mock):
        BUNDLE_UUID = uuid.UUID('12345678123456781234567812345678')
        store = SnapshotRepo()
        file_mapping = {
            'test.html': HTML_FILE,
            'test.txt': TEXT_FILE,
        }
        snapshot = store.create(BUNDLE_UUID, file_mapping)
        self.assertEqual(snapshot.bundle_uuid, BUNDLE_UUID)
        self.assertEqual(
            snapshot.files,
            {
                'test.html': FileInfo(
                    path='test.html',
                    public=False,
                    size=25,
                    hash_digest=create_hash(HTML_CONTENT_BYTES).digest(),
                ),
                'test.txt': FileInfo(
                    path='test.txt',
                    public=False,
                    size=17,
                    hash_digest=create_hash(TEXT_CONTENT_BYTES).digest(),
                ),
            }
        )

        # Test our Django Signal for external notification
        snapshot_created_mock.assert_called_with(
            SnapshotRepo,
            bundle_uuid=BUNDLE_UUID,
            hash_digest=mock.ANY,
        )

        # Make sure we can pull the Snapshot back out of the BundleStore
        # (i.e. it was actually persisted).
        self.assertEqual(snapshot, store.get(BUNDLE_UUID, snapshot.hash_digest))

    @mock.patch('blockstore.apps.bundles.store.snapshot_created.send')
    def test_multiple_snapshots(self, snapshot_created_mock):
        BUNDLE_UUID = uuid.UUID('02345678123456781234567812345678')
        store = SnapshotRepo()
        snapshot_1 = store.create(BUNDLE_UUID, {'test.txt': TEXT_FILE})
        self.assertEqual(
            snapshot_created_mock.call_args[1]['hash_digest'],
            snapshot_1.hash_digest
        )
        snapshot_2 = store.create(BUNDLE_UUID, {'renamed.txt': TEXT_FILE})
        self.assertEqual(
            snapshot_created_mock.call_args[1]['hash_digest'],
            snapshot_2.hash_digest
        )

        self.assertEqual(snapshot_1.bundle_uuid, snapshot_2.bundle_uuid)
        self.assertNotEqual(snapshot_1, snapshot_2)
        self.assertNotEqual(snapshot_1.hash_digest, snapshot_2.hash_digest)
        self.assertEqual(
            snapshot_1.files['test.txt'].hash_digest,
            snapshot_2.files['renamed.txt'].hash_digest,
        )

    def test_snapshot_not_found(self):
        store = SnapshotRepo()
        bundle_uuid = uuid.UUID('00000000000000000000000000000000')
        with self.assertRaises(Snapshot.NotFoundError):
            store.get(bundle_uuid, create_hash().digest())


@isolate_test_storage
class TestDrafts(SimpleTestCase):
    """Test Draft CRUD + commit operations"""

    def setUp(self):
        super().setUp()
        bundle_uuid = uuid.UUID('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        draft_uuid = uuid.UUID('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')

        draft_name = 'studio_draft'
        file_mapping = {
            'test.html': HTML_FILE,
            'test.txt': TEXT_FILE,
        }
        self.snapshot_repo = SnapshotRepo()
        self.draft_repo = DraftRepo(self.snapshot_repo)
        self.snapshot = self.snapshot_repo.create(bundle_uuid, file_mapping)
        self.draft = self.draft_repo.create(
            draft_uuid, bundle_uuid, draft_name, self.snapshot
        )

    def test_draft_with_no_base_snapshot(self):
        """The first time a Draft is created, it won't have a base snapshot."""
        bundle_uuid = uuid.UUID('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        draft_uuid = uuid.UUID('cccccccccccccccccccccccccccccccc')
        created_draft = self.draft_repo.create(
            draft_uuid, bundle_uuid, 'new_draft', base_snapshot=None
        )
        retrieved_draft = self.draft_repo.get(draft_uuid)
        self.assertEqual(created_draft, retrieved_draft)
        self.assertIsNone(retrieved_draft.base_snapshot)
        self.assertEqual(retrieved_draft.files, {})

    def test_empty_draft(self):
        """Test that the basic data was written properly in setUp."""
        # Make sure the persisted Draft is retrieved properly.
        self.assertEqual(self.draft, self.draft_repo.get(self.draft.uuid))

        # The Draft was just created and has no changes, so the files it has
        # should be identical to what's already in the Snapshot it's based on.
        self.assertEqual(self.snapshot.files, self.draft.files)

        # Any file that a Draft doesn't overwrite should return the same URL as
        # what's in the Snapshot.
        for file_path in self.draft.files:
            self.assertEqual(
                self.draft_repo.url(self.draft, file_path),
                self.snapshot_repo.url(self.snapshot, file_path)
            )

    def test_basic_commit(self):
        """Make modifications and commit them."""
        modified_draft = self.draft_repo.update(
            draft_uuid=self.draft.uuid,
            files={
                'test.txt': ContentFile(b"This is draft text content")
            }
        )
        # Make sure the second draft persisted properly.
        self.assertEqual(modified_draft, self.draft_repo.get(self.draft.uuid))
        self.assertEqual(
            self.draft_repo.url(modified_draft, 'test.html'),
            self.snapshot_repo.url(modified_draft.base_snapshot, 'test.html')
        )
        self.assertNotEqual(
            self.draft_repo.url(modified_draft, 'test.txt'),
            self.snapshot_repo.url(modified_draft.base_snapshot, 'test.txt')
        )
        self.assertIsNotNone(self.draft_repo.url(modified_draft, 'test.txt'))

        # Opening the modified file via the DraftRepo's open() should give the
        # new data.
        self.assertEqual(
            self.draft_repo.open(modified_draft, 'test.txt').read(),
            b"This is draft text content",
        )
        # But opening the unmodified file should give the same result as asking
        # for that data from the base snapshot.
        self.assertEqual(
            self.draft_repo.open(modified_draft, 'test.html').read(),
            self.snapshot_repo.open(modified_draft.base_snapshot, 'test.html').read(),
        )

        # Create a new Snapshot from the Draft
        new_snapshot, updated_draft = self.draft_repo.commit(modified_draft)
        self.assertDictEqual(
            new_snapshot.files,
            updated_draft.composed_files(),
        )
        self.assertEqual(new_snapshot.files['test.txt'].size, 26)

    def test_partial_commit(self):
        modified_draft = self.draft_repo.update(
            draft_uuid=self.draft.uuid,
            files={
                'sample/committed.txt': ContentFile(b"This will be committed."),
                'sample/also_committed.txt': ContentFile(b"This will be committed."),
                'sample/uncomitted.txt': ContentFile(b"This won't be committed."),
            }
        )
        new_snapshot, updated_draft = self.draft_repo.commit(
            modified_draft,
            paths=['sample/committed.txt', 'sample/also_committed.txt']
        )
        self.assertIn('sample/committed.txt', new_snapshot.files)
        self.assertIn('sample/also_committed.txt', new_snapshot.files)
        self.assertNotIn('sample/uncomitted.txt', new_snapshot.files)

        self.assertIn('sample/uncomitted.txt', updated_draft.files_to_overwrite)
        self.assertNotIn('sample/committed.txt', updated_draft.files_to_overwrite)
        self.assertNotIn('sample/also_committed.txt', updated_draft.files_to_overwrite)

    def test_delete_file(self):
        self.draft_repo.update(
            draft_uuid=self.draft.uuid,
            files={
                'new_file.txt': ContentFile(b"We're just going to delete this.")
            }
        )
        new_draft = self.draft_repo.update(
            draft_uuid=self.draft.uuid,
            files={
                'test.txt': None,      # Stage delete from underlying Snapshot
                'new_file.txt': None,  # Delete the draft-only file.
            }
        )
        self.assertIsNone(self.draft_repo.open(new_draft, 'test.txt'))
        self.assertIsNone(self.draft_repo.url(new_draft, 'test.txt'))
        self.assertIsNone(self.draft_repo.open(new_draft, 'new_file.txt'))
        self.assertIsNone(self.draft_repo.url(new_draft, 'new_file.txt'))

    def test_delete_draft(self):
        self.draft_repo.update(
            draft_uuid=self.draft.uuid,
            files={
                "will_also_be_deleted.txt": ContentFile(b"File to delete.")
            }
        )
        self.draft_repo.delete(self.draft.uuid)
        with self.assertRaises(StagedDraft.NotFoundError):
            self.draft_repo.get(self.draft.uuid)


class TestTransitiveLinks(unittest.TestCase):
    """Test multiple levels of linking..."""

    def _create_dep(self, bundle_uuid, version=1):
        return Dependency(
            bundle_uuid=bundle_uuid,
            version=version,
            snapshot_digest=create_hash(
                bundle_uuid.bytes + version.to_bytes(2, byteorder='big')
            )
        )

    def setUp(self):
        """
        The dependencies set up here look like:

        Course >
            Content Lib >
                Problem Lib
                Video Lib
        """
        super().setUp()
        self.video_lib_bundle_uuid = uuid.UUID(int=1)
        self.problem_lib_bundle_uuid = uuid.UUID(int=2)
        self.content_lib_bundle_uuid = uuid.UUID(int=3)
        self.course_bundle_uuid = uuid.UUID(int=4)

        # Structures for Content Library that wants to Link to Videos Library
        self.video_lib_dep = self._create_dep(self.video_lib_bundle_uuid)
        self.link_to_video_lib = Link(
            name='videos',
            direct_dependency=self.video_lib_dep,
            indirect_dependencies=[],
        )
        self.problem_lib_dep = self._create_dep(self.problem_lib_bundle_uuid)
        self.link_to_problem_lib = Link(
            name='problems',
            direct_dependency=self.problem_lib_dep,
            indirect_dependencies=[],
        )
        # This is the LinkCollection that lives in the Content Library
        self.links_for_content_lib = LinkCollection(
            bundle_uuid=self.content_lib_bundle_uuid,
            links=[self.link_to_video_lib, self.link_to_problem_lib],
        )

        # Course will pull in Content Library, which will pull in other deps
        self.content_lib_dep = self._create_dep(self.content_lib_bundle_uuid)
        self.link_to_content_lib = Link(
            name="content_lib",
            direct_dependency=self.content_lib_dep,
            indirect_dependencies=self.links_for_content_lib.all_dependencies(),
        )
        self.links_for_course = LinkCollection(
            bundle_uuid=self.course_bundle_uuid,
            links=[self.link_to_content_lib],
        )

    def test_transitive_dependencies(self):
        indirect_dependencies = self.links_for_course["content_lib"].indirect_dependencies
        assert self.video_lib_dep in indirect_dependencies
        assert self.problem_lib_dep in indirect_dependencies
        assert self.content_lib_dep not in indirect_dependencies
        assert self.content_lib_dep == self.links_for_course["content_lib"].direct_dependency

    def test_link_version_bump(self):
        content_lib_dep_v2 = self._create_dep(self.content_lib_bundle_uuid, 2)
        Link(
            name=self.link_to_content_lib.name,
            direct_dependency=content_lib_dep_v2,
            indirect_dependencies=self.link_to_content_lib.indirect_dependencies,
        )

    def test_cycle_detection(self):
        with self.assertRaises(ValueError):
            self.links_for_course.with_updated_link(
                Link(
                    name="circular_link",
                    direct_dependency=self.course_bundle_uuid,
                    indirect_dependencies=[],
                )
            )
