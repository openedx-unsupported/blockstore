""" Tests for api v1 views. """
from future.moves.urllib.parse import urlencode

from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory

from tagstore.backends.django import DjangoTagstore
from tagstore.models import EntityId


class ViewsBaseTestCase(TestCase):
    """ Base class for tests. """

    def setUp(self):

        super().setUp()

        self.client = APIClient()
        self.request_factory = APIRequestFactory()

        self.tagstore = DjangoTagstore()

        self.taxonomy = self.tagstore.create_taxonomy("This Taxonomy")
        self.tags = [
            self.taxonomy.add_tag('tag1'),
            self.taxonomy.add_tag('tag2'),
        ]

        self.entity = EntityId(entity_type='xblock', external_id='some-resource-uri')
        for t in self.tags:
            self.tagstore.add_tag_to(t, self.entity)

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


class EntityTagViewSetTestCase(ViewsBaseTestCase):
    """ Tests for EntityTagViewSet. """

    def test_list(self):

        response = self.response('tagstore:apiv1:entitytags-list', kwargs={
            'external_id': self.entity.external_id
        })

        self.assertIn('tags', response.data)
        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)
        self.assertIn('taxonomy_uid', response.data['tags'][0])
        self.assertIn('taxonomy_name', response.data['tags'][0])
        self.assertIn('tag', response.data['tags'][0])
        self.assertEqual(response.data['tags'][0]['tag'], 'tag1')

    def test_query_params_for_taxonomy(self):

        response = self.response('tagstore:apiv1:entitytags-list', kwargs={
            'external_id': self.entity.external_id,
        }, query_params={'taxonomies': self.taxonomy.uid})

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)

    def test_query_params_for_taxonomy_by_name(self):

        response = self.response('tagstore:apiv1:entitytags-list', kwargs={
            'external_id': self.entity.external_id,
        }, query_params={'taxonomies': self.taxonomy.name})

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)
