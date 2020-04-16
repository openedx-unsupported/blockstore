""" Tests for api v1 views. """
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from tagstore.backends.django import DjangoTagstore
from tagstore.models import EntityId

User = get_user_model()


class ViewsBaseTestCase(TestCase):
    """ Base class for tests. """

    def setUp(self):

        super().setUp()

        self.client = APIClient()
        test_user = User.objects.create(username='test-service-user')
        token = Token.objects.create(user=test_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.tagstore = DjangoTagstore()

        self.taxonomy = self.tagstore.create_taxonomy("This Taxonomy")
        self.tags = [
            self.taxonomy.add_tag('tag1'),
            self.taxonomy.add_tag('tag2'),
        ]

        self.entity = EntityId(entity_type='xblock', external_id='some-resource-uri')
        for t in self.tags:
            self.tagstore.add_tag_to(t, self.entity)

    def response(self, view_name, kwargs=None, method='get', query_params=None,
                 expected_response_code=200, body=None, **method_kwargs):
        """
        Returns a response with the wsgi_request containing any given query params.
        """
        url = reverse(view_name, kwargs=kwargs)
        if query_params:
            url = '{}?{}'.format(url, urlencode(query_params))

        response = getattr(self.client, method)(url, body, **method_kwargs)
        self.assertEqual(response.status_code, expected_response_code)
        return response


class EntityTagViewSetTestCase(ViewsBaseTestCase):
    """ Tests for EntityTagViewSet. """

    def test_list(self):

        response = self.response('tagstore:apiv1:entity-tags', kwargs={
            'pk': self.entity.external_id,
            'entity_type': self.entity.entity_type,
        })

        self.assertIn('tags', response.data)
        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)
        self.assertIn('taxonomy_uid', response.data['tags'][0])
        self.assertIn('taxonomy_name', response.data['tags'][0])
        self.assertIn('tag', response.data['tags'][0])
        self.assertEqual(response.data['tags'][0]['tag'], 'tag1')

    def test_query_params_for_taxonomy(self):

        response = self.response('tagstore:apiv1:entity-tags', kwargs={
            'pk': self.entity.external_id,
            'entity_type': self.entity.entity_type,
        }, query_params={'taxonomies': self.taxonomy.uid})

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)

    def test_query_params_for_taxonomy_by_name(self):

        response = self.response('tagstore:apiv1:entity-tags', kwargs={
            'pk': self.entity.external_id,
            'entity_type': self.entity.entity_type,
        }, query_params={'taxonomies': self.taxonomy.name})

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 2)

    def test_post(self):
        body = {
            'tags': ['bunch', 'of', 'silly', 'tags']}

        response = self.response('tagstore:apiv1:entity-tags', kwargs={
            'pk': self.entity.external_id,
            'entity_type': self.entity.entity_type,
        }, expected_response_code=201, body=body, method='post')

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 6)

    def test_post_with_complex_tag_json(self):
        body = {
            'tags': [
                {
                    'taxonomy_uid': self.taxonomy.uid,
                    'tag': 'test',
                },
                {
                    'taxonomy_uid': self.taxonomy.uid,
                    'tag': 'test3',
                    'parent': 'test',
                }
            ]}

        response = self.response('tagstore:apiv1:entity-tags', kwargs={
            'pk': self.entity.external_id,
            'entity_type': self.entity.entity_type,
        }, expected_response_code=201, body=body, method='post', format='json')

        self.assertTrue(isinstance(response.data['tags'], list))
        self.assertEqual(len(response.data['tags']), 4)
        self.assertTrue(any(x['tag'] == 'test' for x in response.data['tags']))
