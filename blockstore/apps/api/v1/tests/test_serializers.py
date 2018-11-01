""" Tests for api v1 serializers. """

from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIRequestFactory

from blockstore.apps.bundles.tests.factories import (
    BundleFactory, BundleVersionFactory, CollectionFactory, FileInfoFactory
)
from ..serializers.bundles import BundleSerializer, BundleVersionSerializer
from ..serializers.collections import CollectionSerializer
from ..serializers.snapshots import FileInfoSerializer


class SerializerBaseTestCase(TestCase):

    def setUp(self):

        super().setUp()

        self.request_factory = APIRequestFactory()

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


class BundleSerializerTestCase(SerializerBaseTestCase):

    def test_bundle_serializer_data(self):

        bundle_serializer = BundleSerializer(
            self.bundle, context={'request': self.request_factory.get('/')}
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

    def test_bundle_version_serializer_data(self):

        bundle_version_serializer = BundleVersionSerializer(
            self.bundle_version, context={'request': self.request_factory.get('/')}
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

    def test_collection_serializer_data(self):

        collection_serializer = CollectionSerializer(
            self.collection, context={'request': self.request_factory.get('/')}
        )

        self.assertSequenceEqual(list(collection_serializer.data.keys()), [
            'title', 'url', 'uuid'
        ])

        self.assertEqual(collection_serializer.data['title'], 'Collection 1')
        self.assertEqual(collection_serializer.data['uuid'], str(self.collection.uuid))

        self.assertIn('/collections/{}/'.format(self.collection.uuid), collection_serializer.data['url'])


class FileInfoSerializerTestCase(SerializerBaseTestCase):

    def test_file_info_serializer_data(self):
        # pylint: disable=unsubscriptable-object

        request = self.request_factory.get('/')
        request.parser_context = {
            'kwargs': {
                'bundle_uuid': self.bundle.uuid,
            }
        }

        file_info = FileInfoFactory(
            path='a/file.txt', public=False, size=100, hash_digest=bytes('hash_digest', 'utf-8')
        )

        file_info_serializer = FileInfoSerializer(
            file_info, context={'request': request}
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
