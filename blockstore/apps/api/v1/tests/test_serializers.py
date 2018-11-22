""" Tests for api v1 serializers. """

from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIRequestFactory

from blockstore.apps.bundles.tests.factories import (
    BundleFactory, BundleVersionFactory, CollectionFactory, FileInfoFactory
)
from tagstore.backends.tests.factories import EntityFactory

from ..serializers.bundles import BundleSerializer, BundleVersionSerializer
from ..serializers.collections import CollectionSerializer
from ..serializers.entities import EntitySerializer, EntityTagSerializer
from ..serializers.snapshots import FileInfoSerializer


class SerializerBaseTestCase(TestCase):
    """
    Base class for serializer tests.
    """

    def setUp(self):

        super().setUp()

        self.collection = CollectionFactory(title="Collection 1")

        self.bundle = BundleFactory(
            collection=self.collection,
            description='Bundle description.',
            slug='bundle-1',
            title='Bundle 1',
        )

        self.bundle_version = BundleVersionFactory(
            bundle=self.bundle,
            change_description='Update description.',
            snapshot_digest='snapshot_digest',
            version_num=1,
        )

        self.request = APIRequestFactory().get('/')
        self.request.query_params = {}
        self.context = {
            'request': self.request
        }


class BundleSerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the BundleSerializer
    """

    def test_bundle_serializer_data(self):

        bundle_serializer = BundleSerializer(
            self.bundle, context=self.context,
        )

        self.assertSequenceEqual(list(bundle_serializer.data.keys()), [
            'collection', 'description', 'files', 'slug', 'title', 'url', 'uuid', 'versions',
        ])

        self.assertEqual(bundle_serializer.data['description'], 'Bundle description.')
        self.assertEqual(bundle_serializer.data['slug'], 'bundle-1')
        self.assertEqual(bundle_serializer.data['title'], 'Bundle 1')
        self.assertEqual(bundle_serializer.data['uuid'], str(self.bundle.uuid))

        self.assertIn('/collections/{}/'.format(self.collection.uuid), bundle_serializer.data['collection'])
        self.assertIn('/bundles/{}/files/'.format(self.bundle.uuid), bundle_serializer.data['files'])
        self.assertIn('/bundles/{}/'.format(self.bundle.uuid), bundle_serializer.data['url'])


class BundleVersionSerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the BundleVersionSerializer
    """
    def test_bundle_version_serializer_data(self):

        bundle_version_serializer = BundleVersionSerializer(
            self.bundle_version, context=self.context,
        )

        self.assertSequenceEqual(list(bundle_version_serializer.data.keys()), [
            'bundle', 'change_description', 'files', 'url', 'version_num',
        ])

        self.assertEqual(bundle_version_serializer.data['change_description'], 'Update description.')
        self.assertEqual(bundle_version_serializer.data['version_num'], 1)

        self.assertIn('/bundles/{}/'.format(self.bundle.uuid), bundle_version_serializer.data['bundle'])
        self.assertIn(
            '/bundle_versions/{},{}/files/'.format(self.bundle.uuid, self.bundle_version.version_num),
            bundle_version_serializer.data['files']
        )
        self.assertIn(
            '/bundle_versions/{},{}/'.format(self.bundle.uuid, self.bundle_version.version_num),
            bundle_version_serializer.data['files']
        )


class CollectionSerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the CollectionSerializer
    """

    def test_collection_serializer_data(self):

        collection_serializer = CollectionSerializer(
            self.collection, context=self.context,
        )

        self.assertSequenceEqual(list(collection_serializer.data.keys()), [
            'title', 'url', 'uuid'
        ])

        self.assertEqual(collection_serializer.data['title'], 'Collection 1')
        self.assertEqual(collection_serializer.data['uuid'], str(self.collection.uuid))

        self.assertIn('/collections/{}/'.format(self.collection.uuid), collection_serializer.data['url'])


class FileInfoSerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the FileInfoSerializer
    """
    def setUp(self):

        super().setUp()

        self.request.parser_context = {
            'kwargs': {
                'bundle_uuid': self.bundle.uuid,
            }
        }

    def test_file_info_serializer_data(self):
        # pylint: disable=unsubscriptable-object

        file_info = FileInfoFactory(
            path='a/file.txt', public=False, size=100, hash_digest=bytes('hash_digest', 'utf-8')
        )

        file_info_serializer = FileInfoSerializer(
            file_info, context=self.context,
        )

        self.assertSequenceEqual(list(file_info_serializer.data.keys()), [  # pylint: disable=no-member
            'data', 'path', 'public', 'size', 'url'
        ])

        self.assertEqual(file_info_serializer.data['path'], 'a/file.txt')
        self.assertEqual(file_info_serializer.data['public'], False)
        self.assertEqual(file_info_serializer.data['size'], 100)

        self.assertIn(
            '{}{}/data/{}'.format(settings.MEDIA_URL, self.bundle.uuid, file_info.hash_digest.hex()),
            file_info_serializer.data['data']
        )
        self.assertIn(
            'bundles/{}/files/{}/'.format(self.bundle.uuid, file_info.path),
            file_info_serializer.data['url']
        )


class EntitySerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the EntitySerializer
    """

    def test_entity_serializer_data(self):

        entity = EntityFactory(
            entity_type='xblock',
            external_id='some-resource-uri',
        )

        entity_serializer = EntitySerializer(
            entity, context=self.context,
        )

        self.assertSequenceEqual(list(entity_serializer.data.keys()), [
            'id', 'entity_type', 'external_id',
        ])

        self.assertEqual(entity_serializer.data['entity_type'], 'xblock')
        self.assertEqual(entity_serializer.data['external_id'], 'some-resource-uri')


class EntityTagSerializerTestCase(TestCase):
    """
    Tests for the EntityTagSerializer
    """

    def setUp(self):

        super().setUp()

        self.entity_tags = {
            'tags': [
                {
                    'taxonomy_uid': 7,
                    'taxonomy_name': 'Subject Area',
                    'tag': 'Biochemistry'
                },
                {
                    'taxonomy_uid': 9,
                    'taxonomy_name': 'License',
                    'tag': 'CC-BY-SA-4.0'
                }
            ]
        }

    def test_entity_tag_serializer_data(self):

        entity_tag_serializer = EntityTagSerializer(
            self.entity_tags
        )

        self.assertSequenceEqual(list(entity_tag_serializer.data.keys()), ['tags'])
        self.assertSequenceEqual(list(entity_tag_serializer.data['tags'][0].keys()), [
            'taxonomy_uid', 'taxonomy_name', 'tag',
        ])

        self.assertEqual(entity_tag_serializer.data['tags'][0]['taxonomy_uid'], 7)
        self.assertEqual(entity_tag_serializer.data['tags'][0]['taxonomy_name'], 'Subject Area')
