"""
Tests for the api.
"""
import unittest
from uuid import UUID
import crum
from django.test.client import RequestFactory
import pytest

from blockstore.apps import api

# A fake UUID that won't represent any real bundle/draft/collection:
BAD_UUID = UUID('12345678-0000-0000-0000-000000000000')


class BlockstoreApiClientTest(unittest.TestCase):
    """
    Test for the Blockstore API Client.

    The goal of these tests is not to test that Blockstore works correctly, but
    that the API client can interact with it and all the API client methods
    work.
    """
    def setUp(self):
        super().setUp()

        # Mock the current request, so that file URLs can be absolute.
        request = RequestFactory().get('/')
        crum.set_current_request(request)

    # Collections

    def test_nonexistent_collection(self):
        """ Request a collection that doesn't exist -> CollectionNotFound """
        with pytest.raises(api.CollectionNotFound):
            api.get_collection(BAD_UUID)

    def test_collection_crud(self):
        """ Create, Fetch, Update, and Delete a Collection """
        title = "Fire 🔥 Collection"
        # Create:
        coll = api.create_collection(title)
        assert coll.title == title
        assert isinstance(coll.uuid, UUID)
        # Fetch:
        coll2 = api.get_collection(coll.uuid)
        assert coll == coll2
        # Update:
        new_title = "Air 🌀 Collection"
        coll3 = api.update_collection(coll.uuid, title=new_title)
        assert coll3.title == new_title
        coll4 = api.get_collection(coll.uuid)
        assert coll4.title == new_title
        # Delete:
        api.delete_collection(coll.uuid)
        with pytest.raises(api.CollectionNotFound):
            api.get_collection(coll.uuid)

    # Bundles

    def test_nonexistent_bundle(self):
        """ Request a bundle that doesn't exist -> BundleNotFound """
        with pytest.raises(api.BundleNotFound):
            api.get_bundle(BAD_UUID)

    def test_bundle_crud(self):
        """ Create, Fetch, Update, and Delete a Bundle """
        coll = api.create_collection("Test Collection")
        coll2 = api.create_collection("Test Collection 2")
        args = {
            "title": "Water 💧 Bundle",
            "slug": "h2o",
            "description": "Sploosh",
        }
        # Create:
        bundle = api.create_bundle(coll.uuid, **args)
        for attr, value in args.items():
            assert getattr(bundle, attr) == value
        assert isinstance(bundle.uuid, UUID)
        # Fetch:
        bundle2 = api.get_bundle(bundle.uuid)
        assert bundle == bundle2
        # Update:
        new_description = "Water Nation Bending Lessons"
        bundle3 = api.update_bundle(bundle.uuid, description=new_description, collection_uuid=coll2.uuid)
        assert bundle3.description == new_description
        bundle4 = api.get_bundle(bundle.uuid)
        assert bundle4.description == new_description
        # Delete:
        api.delete_bundle(bundle.uuid)
        with pytest.raises(api.BundleNotFound):
            api.get_bundle(bundle.uuid)

    def test_get_bundles(self):
        """ Fetch multiple bundles, and filter by text """
        coll = api.create_collection("Test Collection")
        water_bundle = api.create_bundle(
            coll.uuid,
            title="Water 💧 Bundle",
            slug="h2o",
            description="Sploosh",
        )
        air_bundle = api.create_bundle(
            coll.uuid,
            title="Air 🌀 Bundle",
            slug="no2",
            description="Whoosh",
        )
        fire_bundle = api.create_bundle(
            coll.uuid,
            title="Fire 🔥 Bundle",
            slug="burn",
            description="Crackle",
        )

        # Fetch multiple, and limit using text match
        bundles = api.get_bundles([water_bundle.uuid, air_bundle.uuid, fire_bundle.uuid], text_search='oosh')
        assert len(bundles) == 2
        assert air_bundle in bundles
        assert water_bundle in bundles
        assert fire_bundle not in bundles

    def test_update_bundle_invalid_fields(self):
        """ Updating bundle with unexpected fields -> ValueError """
        coll = api.create_collection("Test Collection")
        bundle = api.create_bundle(
            coll.uuid,
            title="Water 💧 Bundle",
            slug="h2o",
            description="Sploosh",
        )
        with pytest.raises(ValueError):
            api.update_bundle(bundle.uuid, invalid_field='Some invalid field value')

    # Drafts, files, and reading/writing file contents:

    def test_nonexistent_draft(self):
        """ Request a draft that doesn't exist -> DraftNotFound """
        with pytest.raises(api.DraftNotFound):
            api.get_draft(BAD_UUID)

    def test_drafts_and_files(self):
        """
        Test creating, reading, writing, committing, and reverting drafts and
        files.
        """
        coll = api.create_collection("Test Collection")
        bundle = api.create_bundle(coll.uuid, title="Earth 🗿 Bundle", slug="earth", description="another test bundle")
        # Create a draft
        draft = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft")
        assert draft.bundle_uuid == bundle.uuid
        assert draft.name == 'test-draft'
        assert draft.updated_at.year >= 2019
        # And retrieve it again:
        draft2 = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft")
        assert draft == draft2
        # Also test retrieving using get_draft
        draft3 = api.get_draft(draft.uuid)
        assert draft == draft3

        # Write a file into the bundle:
        api.write_draft_file(draft.uuid, "test.txt", b"initial version")
        # Now the file should be visible in the draft:
        draft_contents = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        assert draft_contents == b'initial version'
        api.commit_draft(draft.uuid)

        # Write a new version into the draft:
        api.write_draft_file(draft.uuid, "test.txt", b"modified version")
        published_contents = api.get_bundle_file_data(bundle.uuid, "test.txt")
        assert published_contents == b'initial version'
        draft_contents2 = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        assert draft_contents2 == b'modified version'

        file_info2 = api.get_bundle_file_metadata(bundle.uuid, "test.txt", use_draft=draft.name)
        assert file_info2.url.startswith('http://testserver')
        assert file_info2.path == 'test.txt'
        assert file_info2.size == len(b'modified version')
        assert file_info2.hash_digest == b'oM\xac\xfcD\xd2F\x11\xd2\xa7;\xff\x88\x8eS\x12\xc6\xe3\xfb\\'
        assert api.get_bundle_files_dict(bundle.uuid, use_draft=draft.name) == {'test.txt': file_info2}

        # Now delete the draft:
        api.delete_draft(draft.uuid)
        draft_contents3 = api.get_bundle_file_data(bundle.uuid, "test.txt", use_draft=draft.name)
        # Confirm the file is now reset:
        assert draft_contents3 == b'initial version'

        # Finaly, test the get_bundle_file* methods:
        file_info1 = api.get_bundle_file_metadata(bundle.uuid, "test.txt")
        assert file_info1.url.startswith('http://testserver')
        assert file_info1.path == 'test.txt'
        assert file_info1.size == len(b'initial version')
        assert file_info1.hash_digest == 'a45a5c6716276a66c4005534a51453ab16ea63c4'

        assert list(api.get_bundle_files(bundle.uuid)) == [file_info1]
        assert api.get_bundle_files_dict(bundle.uuid) == {'test.txt': file_info1}
        assert api.get_bundle_files_dict(bundle.uuid, use_draft=draft.name) == {'test.txt': file_info1}

        with pytest.raises(api.BundleFileNotFound):
            api.get_bundle_file_metadata(bundle.uuid, "nonexistent.txt")

    def test_bundle_version(self):
        """
        Test creating, reading, and writing bundle versions and files
        """
        coll = api.create_collection("Test Collection")
        bundle = api.create_bundle(
            coll.uuid,
            title="Water 💧 Bundle",
            slug="h2o",
            description="Sploosh",
        )

        no_files = api.get_bundle_version_files(bundle.uuid, 0)
        assert no_files == []

        # Create and commit a draft
        draft = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft")
        api.commit_draft(draft.uuid)

        # Fetch latest bundle version
        latest_bundle_version = api.get_bundle_version(bundle.uuid)
        bundle_version = api.get_bundle_version(bundle.uuid, 1)
        assert bundle_version == latest_bundle_version
        assert bundle_version.bundle_uuid == bundle.uuid
        assert bundle_version.version == 1
        assert bundle_version.files == {}
        assert bundle_version.links == {}

        # Unavailable version throws error
        with pytest.raises(api.BundleVersionNotFound):
            api.get_bundle_version(bundle.uuid, 2)

        # Add file to a new draft
        draft2 = api.get_or_create_bundle_draft(bundle.uuid, draft_name="test-draft-files")
        api.write_draft_file(draft2.uuid, "test.txt", b"initial version")
        api.commit_draft(draft2.uuid)

        # Fetch this bundle version's files
        files = api.get_bundle_version_files(bundle.uuid, 2)
        assert len(files) == 1
        for bundle_file in files:
            assert bundle_file.url.startswith('http://testserver')
            assert bundle_file.path == 'test.txt'
            assert bundle_file.size == len(b'initial version')
            assert bundle_file.hash_digest == 'a45a5c6716276a66c4005534a51453ab16ea63c4'

    # Links

    def test_links(self):
        """
        Test operations involving bundle links.
        """
        coll = api.create_collection("Test Collection")
        # Create two library bundles and a course bundle:
        lib1_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="lib1")
        lib1_draft = api.get_or_create_bundle_draft(lib1_bundle.uuid, draft_name="test-draft")
        lib2_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="lib2")
        lib2_draft = api.get_or_create_bundle_draft(lib2_bundle.uuid, draft_name="other-draft")
        course_bundle = api.create_bundle(coll.uuid, title="Library 1", slug="course")
        course_draft = api.get_or_create_bundle_draft(course_bundle.uuid, draft_name="test-draft")
        assert api.get_bundle_version_links(course_bundle.uuid, 0) == {}

        # To create links, we need valid BundleVersions, which requires having committed at least one change:
        api.write_draft_file(lib1_draft.uuid, "lib1-data.txt", "hello world")
        api.commit_draft(lib1_draft.uuid)  # Creates version 1
        api.write_draft_file(lib2_draft.uuid, "lib2-data.txt", "hello world")
        api.commit_draft(lib2_draft.uuid)  # Creates version 1

        # Lib2 has no links:
        assert not api.get_bundle_links(lib2_bundle.uuid)

        # Create a link from lib2 to lib1
        link1_name = "lib2_to_lib1"
        api.set_draft_link(lib2_draft.uuid, link1_name, lib1_bundle.uuid, version=1)
        # Now confirm the link exists in the draft:
        lib2_draft_links = api.get_bundle_links(lib2_bundle.uuid, use_draft=lib2_draft.name)
        assert link1_name in lib2_draft_links
        assert lib2_draft_links[link1_name].direct.bundle_uuid == lib1_bundle.uuid
        assert lib2_draft_links[link1_name].direct.version == 1
        # Now commit the change to lib2:
        api.commit_draft(lib2_draft.uuid)  # Creates version 2

        # Now create a link from course to lib2
        link2_name = "course_to_lib2"
        api.set_draft_link(course_draft.uuid, link2_name, lib2_bundle.uuid, version=2)
        api.commit_draft(course_draft.uuid)

        # And confirm the link exists in the resulting bundle version:
        course_links = api.get_bundle_links(course_bundle.uuid)
        assert link2_name in course_links
        assert course_links[link2_name].direct.bundle_uuid == lib2_bundle.uuid
        assert course_links[link2_name].direct.version == 2
        # And since the links go course->lib2->lib1, course has an indirect link to lib1:
        assert course_links[link2_name].indirect[0].bundle_uuid == lib1_bundle.uuid
        assert course_links[link2_name].indirect[0].version == 1

        bundle_version_links = api.get_bundle_version_links(course_bundle.uuid, None)
        assert bundle_version_links == course_links

        # Test deleting a link from course's draft:
        api.set_draft_link(course_draft.uuid, link2_name, None, None)
        assert not api.get_bundle_links(course_bundle.uuid, use_draft=course_draft.name)

        # Finally, delete the draft from the course and ensure the links are unchanged
        api.delete_draft(course_draft.uuid)
        course_links2 = api.get_bundle_links(course_bundle.uuid, use_draft=course_draft.name)
        assert course_links == course_links2
