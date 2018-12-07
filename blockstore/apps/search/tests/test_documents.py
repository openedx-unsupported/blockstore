""" Tests for views. """

from elasticsearch_dsl import Object

from ..core.serializers import FieldSetSerializer
from ..core.tests.test_base import DocumentBaseTestCase
from ..documents import BlockDocument
from ..fieldsets import (
    AnalyticsFieldSet,
    AuthorshipFieldSet,
    EntityFieldSet,
    OwnernershipFieldSet,
    SummaryFieldSet,
    TagsFieldSet,
)


class BlockDocumentTestCase(DocumentBaseTestCase):
    """ Tests for BlockDocument. """

    document_class = BlockDocument

    def test_fieldsets_initialization(self):

        for field_set_class in BlockDocument.FIELD_SETS:

            document_field = BlockDocument._doc_type.mapping[field_set_class.name]  # pylint: disable=protected-access
            self.assertIsInstance(document_field, Object)

            document_serializer = BlockDocument.Serializer()
            self.assertIsInstance(document_serializer.fields[field_set_class.name], FieldSetSerializer)

    def test_document_create(self):

        document = BlockDocument(
            analytics=AnalyticsFieldSet.Document(favorites=8, remixes=2, views=200),
            authorship=AuthorshipFieldSet.Document(author_ids=['First author', 'Second author']),
            entity=EntityFieldSet.Document(type='xblock', id='block-v1:Blockstore+Course+type@html+block@030e35c'),
            ownership=OwnernershipFieldSet.Document(org_id='Blockstore'),
            summary=SummaryFieldSet.Document(title='Introduction', description='Welcome!', image='http//image.png'),
            tags=TagsFieldSet.Document(paths=['15:easy:', '200:animal:mammal:lion:']),
        )
        document.save()
