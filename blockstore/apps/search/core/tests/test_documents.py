""" Tests for documents. """

from elasticsearch.exceptions import RequestError
import pytest

from .test_base import DocumentBaseTestCase


class DocumentTestCase(DocumentBaseTestCase):
    """ Tests for Document. """

    def test_create_document(self):

        document = self.document_class()
        document.save()
        self.assertEqual(len(document.uuid), 20)
        self.assertEqual(document.uuid, document.meta.id)

        document = self.document_class.get(document.uuid)
        self.assertIsInstance(document, self.document_class)

    def test_adding_unmapped_fields_raises_error(self):

        document = self.document_class(shape='round')
        with pytest.raises(RequestError):
            document.save()
