""" Helper classes for tests. """

import uuid

from django.test import TestCase
from elasticsearch_dsl import Index
from future.moves.urllib.parse import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from ..documents import Document


class DocumentBaseTestCase(TestCase):
    """ Base class for Document tests. """

    document_class = Document
    index_class = Index

    def setUp(self):
        super().setUp()
        self.index = self.index_class(str(uuid.uuid4()))
        self.index.document(self.document_class)
        self.document_class._index = self.index  # pylint: disable=protected-access
        self.index.save()

    def tearDown(self):
        self.index.delete(ignore=404)
        super().tearDown()


class ViewsBaseTestCase(DocumentBaseTestCase):
    """ Base class for DocumentViewSet tests. """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def response(
        self, view_name, kwargs=None, method='get', query_params=None, expected_response_code=200, **method_kwargs
    ):
        """ Make a request with the APIClient and return the response. """

        url = reverse(view_name, kwargs=kwargs)
        if query_params:
            url = '{}?{}'.format(url, urlencode(query_params))
        response = getattr(self.client, method)(url, **method_kwargs)
        self.assertEqual(response.status_code, expected_response_code)
        return response
