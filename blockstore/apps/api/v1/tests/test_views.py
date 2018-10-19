""" Tests for api v1 views. """
from django.test import TestCase
from django.core.files.base import ContentFile
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory

from blockstore.apps.bundles.models import Bundle, BundleVersion, Collection
from blockstore.apps.bundles.store import BundleDataStore

from blockstore.apps.bundles.tests.factories import (
    BundleFactory, CollectionFactory
)

from ..serializers.bundles import BundleSerializer, BundleVersionSerializer
from ..serializers.collections import CollectionSerializer
from ..serializers.snapshots import FileInfoSerializer

from ..views.snapshots import BundleFileReadOnlyViewSet, BundleFileViewSet


HTML_CONTENT_BYTES = b"<p>I am an HTML file!</p>"
TEXT_CONTENT_BYTES = b"I am a text file!"

HTML_FILE = ContentFile(HTML_CONTENT_BYTES)
TEXT_FILE = ContentFile(TEXT_CONTENT_BYTES)


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

    def response(self, view_name, kwargs=None, method='get', **method_kwargs):
        """
        Returns a response with the wsgi_request containing any given query params.
        """
        url = reverse(view_name, kwargs=kwargs)
        response = getattr(self.client, method)(url, **method_kwargs)
        response.wsgi_request.query_params = {}
        if kwargs:
            response.wsgi_request.parser_context = {'kwargs': kwargs}
        return response


class BundleViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleViewSet. """

    def test_list(self):

        response = self.response('api:v1:bundle-list')
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data,
            BundleSerializer(Bundle.objects.all(), context={'request': response.wsgi_request}, many=True).data
        )

    def test_get(self):

        response = self.response('api:v1:bundle-detail', kwargs={'bundle_uuid': self.bundle.uuid})
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            BundleSerializer(self.bundle, context={'request': response.wsgi_request}).data
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            BundleSerializer(self.bundle, context={'request': response.wsgi_request}).data
        )

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
        )

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.data,
            BundleSerializer(
                Bundle.objects.all().order_by('-id').first(), context={'request': response.wsgi_request}
            ).data
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

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            BundleSerializer(
                Bundle.objects.get(uuid=self.bundle.uuid), context={'request': response.wsgi_request}
            ).data
        )
        self.assertEqual(Bundle.objects.all().count(), bundles_count)


class BundleVersionViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleVersionViewSet. """

    def test_list(self):

        response = self.response('api:v1:bundleversion-list')
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data,
            BundleVersionSerializer(
                BundleVersion.objects.all(), context={'request': response.wsgi_request}, many=True
            ).data
        )

    def test_get(self):

        response = self.response('api:v1:bundleversion-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'version_num': self.bundle_version.version_num,
        })
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            BundleVersionSerializer(
                self.bundle_version, context={'request': response.wsgi_request}
            ).data
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            BundleVersionSerializer(
                self.bundle_version, context={'request': response.wsgi_request}
            ).data
        )


class CollectionViewSetTestCase(ViewsBaseTestCase):
    """ Tests for CollectionViewSet. """

    def test_list(self):

        response = self.response('api:v1:collection-list')
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data,
            CollectionSerializer(
                Collection.objects.all(), context={'request': response.wsgi_request}, many=True
            ).data
        )

    def test_get(self):

        response = self.response('api:v1:collection-detail', kwargs={'uuid': self.collection.uuid})
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            CollectionSerializer(
                self.collection, context={'request': response.wsgi_request}
            ).data
        )

    def test_create(self):

        collections_count = Collection.objects.all().count()

        response = self.response(
            'api:v1:collection-list',
            method='post',
            data={'title': 'Collection 2'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.data,
            CollectionSerializer(
                Collection.objects.all().order_by('-id').first(), context={'request': response.wsgi_request}
            ).data
        )
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
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            CollectionSerializer(
                Collection.objects.get(uuid=self.collection.uuid), context={'request': response.wsgi_request}
            ).data
        )
        self.assertEqual(Collection.objects.all().count(), collections_count)


class BundleFileReadOnlyViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleFileReadonlyViewSet. """

    def test_list(self):

        response = self.response('api:v1:bundleversionfile-list', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'version_num': self.bundle_version.version_num,
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data,
            FileInfoSerializer(
                self.bundle_version.snapshot().files.values(),
                context={
                    'detail_view_name': BundleFileReadOnlyViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
                many=True
            ).data
        )

    def test_get(self):

        file_info = list(self.bundle_version.snapshot().files.values())[0]

        response = self.response('api:v1:bundleversionfile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'version_num': self.bundle_version.version_num,
            'path': file_info.path,
        })

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            FileInfoSerializer(
                file_info,
                context={
                    'detail_view_name': BundleFileReadOnlyViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
            ).data
        )


class BundleFileViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BundleFileViewSet. """

    def test_version_not_found(self):
        bundle = BundleFactory(
            collection=self.collection,
            description='Bundle description 2.',
            slug='bundle-2',
            title='Bundle 2',
        )
        response = self.response('api:v1:bundlefile-list', kwargs={'bundle_uuid': bundle.uuid})
        self.assertEqual(response.status_code, 404)

    def test_file_not_found(self):
        response = self.response('api:v1:bundlefile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'path': 'notapath.txt'
        })
        self.assertEqual(response.status_code, 404)

    def test_list(self):

        response = self.response('api:v1:bundlefile-list', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid
        })
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            response.data,
            FileInfoSerializer(
                self.bundle_version.snapshot().files.values(),
                context={
                    'detail_view_name': BundleFileViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
                many=True
            ).data
        )

    def test_get(self):

        file_info = list(self.bundle_version.snapshot().files.values())[0]

        response = self.response('api:v1:bundlefile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'path': file_info.path,
        })
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            FileInfoSerializer(
                file_info,
                context={
                    'detail_view_name': BundleFileViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
            ).data
        )

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
        )

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 1)

        file_info = list(new_bundle_version.snapshot().files.values())[2]

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.data,
            FileInfoSerializer(
                file_info,
                context={
                    'detail_view_name': BundleFileViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
            ).data
        )

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
        )

        new_bundle_version = new_bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 1)

        file_info = list(new_bundle_version.snapshot().files.values())[0]

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.data,
            FileInfoSerializer(
                file_info,
                context={
                    'detail_view_name': BundleFileViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
            ).data
        )

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
        )
        self.assertContains(response, 'No file was submitted', status_code=400)

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
        )
        self.assertEqual(response.status_code, 201)

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files), files_count + 2)

        file_infos = list(new_bundle_version.snapshot().files.values())[-2:]
        self.assertEqual(
            response.data,
            FileInfoSerializer(
                file_infos,
                context={
                    'detail_view_name': BundleFileViewSet.detail_view_name,
                    'request': response.wsgi_request,
                },
                many=True,
            ).data
        )

    def test_delete(self):

        files_count = len(self.bundle.versions.order_by('-version_num').first().snapshot().files)

        file_info = list(self.bundle_version.snapshot().files.values())[0]

        url = reverse('api:v1:bundlefile-detail', kwargs={
            'bundle_uuid': self.bundle_version.bundle.uuid,
            'path': file_info.path,
        })
        response = self.client.delete(url)

        new_bundle_version = self.bundle.versions.order_by('-version_num').first()
        self.assertEqual(len(new_bundle_version.snapshot().files.keys()), files_count - 1)

        self.assertEqual(response.status_code, 204)
