""" Tests for api v1 views. """
from future.moves.urllib.parse import urlencode

import ddt
from django.test import TestCase
from django.core.files.base import ContentFile
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory

from blockstore.apps.bundles.models import Bundle, Collection
from blockstore.apps.bundles.store import BundleDataStore

from blockstore.apps.bundles.tests.factories import (
    BundleFactory, CollectionFactory
)

HTML_CONTENT_BYTES = b"<p>I am an HTML file!</p>"
TEXT_CONTENT_BYTES = b"I am a text file!"

HTML_FILE = ContentFile(HTML_CONTENT_BYTES)
TEXT_FILE = ContentFile(TEXT_CONTENT_BYTES)

HTML_CONTENT_HASH = 'c0c0940e4b3151908b60cecd1ef5e2aa19904676'
TEXT_CONTENT_HASH = 'f51746fee3835cd0d6342d28c2be86105134b2f4'


class ViewsBaseTestCase(TestCase):
    """ Base class for tests. """

    def setUp(self):

        super().setUp()

        self.client = APIClient()
        self.request_factory = APIRequestFactory()

        self.collection = CollectionFactory(title="Collection 1")

        self.bundle = BundleFactory(
            collection=self.collection,
            description='Bundle description 1.',
            slug='bundle-1',
            title='Bundle 1',
        )

        self.data_store = BundleDataStore()
        self.data_store.create_snapshot(self.bundle.uuid, {
            'a/file-1.html': HTML_FILE,
            'b/file-2.txt': TEXT_FILE,
        })

        self.bundle_version = self.bundle.versions.first()

    def response(self, view_name, kwargs=None, method='get', query_params=None, expected_response_code=200,
                 **method_kwargs):
        """
        Returns a response with the wsgi_request containing any given query params.
        """
        url = reverse(view_name, kwargs=kwargs)
        if query_params:
            url = '{}?{}'.format(url, urlencode(query_params))

        response = getattr(self.client, method)(url, **method_kwargs)
        self.assertEqual(response.status_code, expected_response_code)
        return response


@ddt.ddt
class BundleViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleViewSet. """

    @ddt.data(
        {}, {'expand': 'files'},
    )
    def test_list(self, query_params):
        """
        The bundle-list view displays a list of all bundles, and ignores the ?expand=files query param.
        """
        response = self.response('api:v1:bundle-list', query_params=query_params)
        self.assertListEqual(response.data, [{
            'collection': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'description': 'Bundle description 1.',
            'files': 'http://testserver/api/v1/bundles/{}/files/'.format(self.bundle.uuid),
            'slug': 'bundle-1',
            'title': 'Bundle 1',
            'url': 'http://testserver/api/v1/bundles/{}/'.format(self.bundle.uuid),
            'uuid': '{}'.format(self.bundle.uuid),
            'versions': [
                'http://testserver/api/v1/bundle_versions/{},1/'.format(self.bundle.uuid),
            ]
        }])

    @ddt.data(
        {}, {'expand': 'files'},
    )
    def test_get(self, query_params):
        """
        The bundle-detail view displays a single bundle.

        Shows the expanded files data if ?expand=files query param is provided.
        """
        response = self.response(
            'api:v1:bundle-detail',
            kwargs={'bundle_uuid': self.bundle.uuid},
            query_params=query_params,
        )
        expected_data = {
            'collection': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'description': 'Bundle description 1.',
            'files': 'http://testserver/api/v1/bundles/{}/files/'.format(self.bundle.uuid),
            'slug': 'bundle-1',
            'title': 'Bundle 1',
            'url': 'http://testserver/api/v1/bundles/{}/'.format(self.bundle.uuid),
            'uuid': '{}'.format(self.bundle.uuid),
            'versions': [
                'http://testserver/api/v1/bundle_versions/{},1/'.format(self.bundle.uuid),
            ]
        }
        if query_params.get('expand', '') == 'files':
            expected_data['files'] = [
                {
                    'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
                    'path': 'a/file-1.html',
                    'public': False,
                    'size': 25,
                    'url': 'http://testserver/api/v1/bundles/{}/files/a/file-1.html/'.format(self.bundle.uuid),
                }, {
                    'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, TEXT_CONTENT_HASH),
                    'path': 'b/file-2.txt',
                    'public': False,
                    'size': 17,
                    'url': 'http://testserver/api/v1/bundles/{}/files/b/file-2.txt/'.format(self.bundle.uuid),
                },
            ]
        self.assertDictEqual(response.data, expected_data)

    def test_create(self):

        bundles_count = Bundle.objects.all().count()
        response = self.response(
            'api:v1:bundle-list',
            method='post',
            data={
                'collection': reverse('api:v1:collection-detail', kwargs={'uuid': self.collection.uuid}),
                'description': 'Bundle description 2.',
                'slug': 'bundle-2',
                'title': 'Bundle 2',
            },
            format='json',
            expected_response_code=201,
        )
        new_bundle_uuid = response.data.get('uuid')
        self.assertDictEqual(response.data, {
                'collection': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
                'description': 'Bundle description 2.',
                'files': 'http://testserver/api/v1/bundles/{}/files/'.format(new_bundle_uuid),
                'slug': 'bundle-2',
                'title': 'Bundle 2',
                'url': 'http://testserver/api/v1/bundles/{}/'.format(new_bundle_uuid),
                'uuid': new_bundle_uuid,
                'versions': [],
            }
        )
        self.assertEqual(Bundle.objects.all().count(), bundles_count + 1)

    def test_update(self):

        bundles_count = Bundle.objects.all().count()
        response = self.response(
            'api:v1:bundle-detail',
            kwargs={
                'bundle_uuid': self.bundle.uuid,
            },
            method='patch',
            data={
                'description': 'Bundle description 2.1.',
                'slug': 'bundle-2-1',
                'title': 'Bundle 2.1',
            },
            format='json',
        )
        self.assertDictEqual(response.data, {
            'collection': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'description': 'Bundle description 2.1.',
            'files': 'http://testserver/api/v1/bundles/{}/files/'.format(self.bundle.uuid),
            'slug': 'bundle-2-1',
            'title': 'Bundle 2.1',
            'url': 'http://testserver/api/v1/bundles/{}/'.format(self.bundle.uuid),
            'uuid': '{}'.format(self.bundle.uuid),
            'versions': [
                'http://testserver/api/v1/bundle_versions/{},1/'.format(self.bundle.uuid),
            ]
        })
        self.assertEqual(Bundle.objects.all().count(), bundles_count)


@ddt.ddt
class BundleVersionViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleVersionViewSet. """

    @ddt.data(
        {}, {'expand': 'files'},
    )
    def test_list(self, query_params):
        """
        The bundleversion-list view displays a list of all bundles, and ignores the ?expand=files query param.
        """
        response = self.response('api:v1:bundleversion-list', query_params=query_params)
        self.assertListEqual(response.data, [{
            'bundle': 'http://testserver/api/v1/bundles/{}/'.format(self.bundle.uuid),
            'change_description': '',
            'files': 'http://testserver/api/v1/bundle_versions/{},1/files/'.format(self.bundle.uuid),
            'url': 'http://testserver/api/v1/bundle_versions/{},1/'.format(self.bundle.uuid),
            'version_num': 1,
        }])

    @ddt.data(
        {}, {'expand': 'files'},
    )
    def test_get(self, query_params):
        """
        The bundleversion-detail view displays a single bundle.

        Shows the expanded files data if ?expand=files query param is provided.
        """
        response = self.response(
            'api:v1:bundleversion-detail',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
                'version_num': self.bundle_version.version_num,
            },
            query_params=query_params,
        )
        expected_data = {
            'bundle': 'http://testserver/api/v1/bundles/{}/'.format(self.bundle.uuid),
            'change_description': '',
            'files': 'http://testserver/api/v1/bundle_versions/{},1/files/'.format(self.bundle.uuid),
            'url': 'http://testserver/api/v1/bundle_versions/{},1/'.format(self.bundle.uuid),
            'version_num': 1,
        }
        if query_params.get('expand', '') == 'files':
            expected_data['files'] = [{
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
                'path': 'a/file-1.html',
                'public': False,
                'size': 25,
                'url': 'http://testserver/api/v1/bundle_versions/{},1/files/a/file-1.html/'.format(self.bundle.uuid),
            }, {
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, TEXT_CONTENT_HASH),
                'path': 'b/file-2.txt',
                'public': False,
                'size': 17,
                'url': 'http://testserver/api/v1/bundle_versions/{},1/files/b/file-2.txt/'.format(self.bundle.uuid),
            }]
        self.assertDictEqual(response.data, expected_data)


class CollectionViewSetTestCase(ViewsBaseTestCase):
    """ Tests for CollectionViewSet. """

    def test_list(self):

        response = self.response('api:v1:collection-list')
        self.assertListEqual(response.data, [{
            'title': 'Collection 1',
            'url': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'uuid': '{}'.format(self.collection.uuid),
        }])

    def test_get(self):

        response = self.response('api:v1:collection-detail', kwargs={'uuid': self.collection.uuid})
        self.assertDictEqual(response.data, {
            'title': 'Collection 1',
            'url': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'uuid': '{}'.format(self.collection.uuid),
        })

    def test_create(self):

        collections_count = Collection.objects.all().count()
        response = self.response(
            'api:v1:collection-list',
            method='post',
            data={'title': 'Collection 2'},
            format='json',
            expected_response_code=201,
        )
        new_collection_uuid = response.data.get('uuid')
        self.assertDictEqual(response.data, {
            'title': 'Collection 2',
            'url': 'http://testserver/api/v1/collections/{}/'.format(new_collection_uuid),
            'uuid': new_collection_uuid,
        })
        self.assertEqual(Collection.objects.all().count(), collections_count + 1)

    def test_update(self):

        collections_count = Collection.objects.all().count()
        response = self.response(
            'api:v1:collection-detail',
            kwargs={'uuid': self.collection.uuid},
            method='patch',
            data={'title': 'Collection 1.1'},
            format='json',
        )
        self.assertDictEqual(response.data, {
            'title': 'Collection 1.1',
            'url': 'http://testserver/api/v1/collections/{}/'.format(self.collection.uuid),
            'uuid': '{}'.format(self.collection.uuid),
        })
        self.assertEqual(Collection.objects.all().count(), collections_count)


class BundleFileReadOnlyViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleFileReadonlyViewSet. """

    def test_list(self):

        response = self.response('api:v1:bundleversionfile-list', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'version_num': self.bundle_version.version_num,
        })
        self.assertListEqual(response.data, [
            {
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
                'path': 'a/file-1.html',
                'public': False,
                'size': 25,
                'url': 'http://testserver/api/v1/bundle_versions/{},1/files/a/file-1.html/'.format(self.bundle.uuid),
            }, {
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, TEXT_CONTENT_HASH),
                'path': 'b/file-2.txt',
                'public': False,
                'size': 17,
                'url': 'http://testserver/api/v1/bundle_versions/{},1/files/b/file-2.txt/'.format(self.bundle.uuid),
            },
        ])

    def test_get(self):

        file_info = list(self.bundle_version.snapshot().files.values())[0]
        response = self.response('api:v1:bundleversionfile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'version_num': self.bundle_version.version_num,
            'path': file_info.path,
        })
        self.assertDictEqual(response.data, {
            'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
            'path': 'a/file-1.html',
            'public': False,
            'size': 25,
            'url': 'http://testserver/api/v1/bundle_versions/{},1/files/a/file-1.html/'.format(self.bundle.uuid),
        })


class BundleFileViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleFileViewSet. """

    def test_version_not_found(self):
        bundle = BundleFactory(
            collection=self.collection,
            description='Bundle description 2.',
            slug='bundle-2',
            title='Bundle 2',
        )
        self.response(
            'api:v1:bundlefile-list',
            kwargs={'bundle_uuid': bundle.uuid},
            expected_response_code=404,
        )

    def test_file_not_found(self):
        self.response(
            'api:v1:bundlefile-detail',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
                'path': 'notapath.txt'
            },
            expected_response_code=404,
        )

    def test_list(self):

        response = self.response('api:v1:bundlefile-list', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid
        })
        self.assertListEqual(response.data, [
            {
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
                'path': 'a/file-1.html',
                'public': False,
                'size': 25,
                'url': 'http://testserver/api/v1/bundles/{}/files/a/file-1.html/'.format(self.bundle.uuid),
            }, {
                'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, TEXT_CONTENT_HASH),
                'path': 'b/file-2.txt',
                'public': False,
                'size': 17,
                'url': 'http://testserver/api/v1/bundles/{}/files/b/file-2.txt/'.format(self.bundle.uuid),
            },
        ])

    def test_get(self):

        file_info = list(self.bundle_version.snapshot().files.values())[0]
        response = self.response('api:v1:bundlefile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'path': file_info.path,
        })
        self.assertDictEqual(response.data, {
            'data': 'http://testserver/media/{}/data/{}'.format(self.bundle.uuid, HTML_CONTENT_HASH),
            'path': 'a/file-1.html',
            'public': False,
            'size': 25,
            'url': 'http://testserver/api/v1/bundles/{}/files/a/file-1.html/'.format(self.bundle.uuid),
        })

    def test_create(self):

        files_count = len(self.bundle.versions.order_by('-version_num').first().snapshot().files)
        response = self.response(
            'api:v1:bundlefile-list',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
            },
            method='post',
            data={
                'path': 'c/file-3.txt', 'data': ContentFile(TEXT_CONTENT_BYTES)
            },
            format='multipart',
            expected_response_code=201,
        )

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 1)

        self.assertDictEqual(response.data, {
            'data': 'http://testserver/media/{}/data/{}'.format(new_bundle_version.bundle.uuid, TEXT_CONTENT_HASH),
            'path': 'c/file-3.txt',
            'public': False,
            'size': 17,
            'url': 'http://testserver/api/v1/bundles/{}/files/c/file-3.txt/'.format(new_bundle_version.bundle.uuid),
        })

    def test_create_new(self):

        files_count = 0
        new_bundle = BundleFactory(
            collection=self.collection,
            description='Bundle description 2.',
            slug='bundle-2',
            title='Bundle 2',
        )

        response = self.response(
            'api:v1:bundlefile-list',
            kwargs={
                'bundle_uuid': new_bundle.uuid,
            },
            method='post',
            data={
                'path': 'c/file-3.txt', 'data': ContentFile(TEXT_CONTENT_BYTES)
            },
            format='multipart',
            expected_response_code=201,
        )

        new_bundle_version = new_bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 1)

        self.assertDictEqual(response.data, {
            'data': 'http://testserver/media/{}/data/{}'.format(new_bundle_version.bundle.uuid, TEXT_CONTENT_HASH),
            'path': 'c/file-3.txt',
            'public': False,
            'size': 17,
            'url': 'http://testserver/api/v1/bundles/{}/files/c/file-3.txt/'.format(new_bundle_version.bundle.uuid),
        })

    def test_create_error(self):

        files_count = len(self.bundle.versions.order_by('-version_num').first().snapshot().files)

        response = self.response(
            'api:v1:bundlefile-list',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
            },
            method='post',
            data={
                'path': 'c/file-3.txt',
            },
            format='multipart',
            expected_response_code=400,
        )
        self.assertListEqual(response.data, [{"data": ["No file was submitted."]}])

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count)

    def test_create_multiple_files(self):

        files_count = len(self.bundle.versions.order_by('-version_num').first().snapshot().files)

        response = self.response(
            'api:v1:bundlefile-list',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
            },
            method='post',
            data={
                'data': [ContentFile(TEXT_CONTENT_BYTES), ContentFile(HTML_CONTENT_BYTES)],
                'path': ['c/file-4.txt', 'c/file-5.html'],
                'public': [True, False]
            },
            format='multipart',
            expected_response_code=201,
        )

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 2)

        self.assertListEqual(response.data, [{
            'data': 'http://testserver/media/{}/data/{}'.format(new_bundle_version.bundle.uuid, TEXT_CONTENT_HASH),
            'path': 'c/file-4.txt',
            'public': True,
            'size': 17,
            'url': 'http://testserver/api/v1/bundles/{}/files/c/file-4.txt/'.format(new_bundle_version.bundle.uuid),
        }, {
            'data': 'http://testserver/media/{}/data/{}'.format(new_bundle_version.bundle.uuid, HTML_CONTENT_HASH),
            'path': 'c/file-5.html',
            'public': False,
            'size': 25,
            'url': 'http://testserver/api/v1/bundles/{}/files/c/file-5.html/'.format(new_bundle_version.bundle.uuid),
        }])

    def test_delete(self):

        files_count = len(self.bundle.versions.order_by('-version_num').first().snapshot().files)
        file_info = list(self.bundle_version.snapshot().files.values())[0]

        response = self.response(
            'api:v1:bundlefile-detail',
            method='delete',
            kwargs={
                'bundle_uuid': self.bundle_version.bundle.uuid,
                'path': file_info.path,
            },
            expected_response_code=204,
        )
        self.assertIsNone(response.data)

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files.keys()), files_count - 1)
