"""
Base Documents for search.
"""
from collections import OrderedDict

from elasticsearch_dsl import (
    Document as ESDocument,
    MetaField,
    Object,
)

from elasticsearch_dsl.document import (
    IndexMeta as ESIndexMeta
)

from .serializers import DocumentSerializer


class IndexMeta(ESIndexMeta):

    def __new__(mcs, name, bases, attrs):

        field_set_serializers = OrderedDict()

        for field_set_class in attrs['FIELD_SETS']:
            # Attach FieldSets to the Document.
            attrs[field_set_class.name] = Object(field_set_class.Document)
            # And their Serializers to the Document Serializer.
            field_set_serializers[field_set_class.name] = field_set_class.Serializer

        new_cls = super().__new__(mcs, name, bases, attrs)
        new_cls.Serializer.field_set_serializers = field_set_serializers
        return new_cls


class Document(ESDocument, metaclass=IndexMeta):
    """
    Base Document class.
    """

    FIELD_SETS = ()

    class Meta:
        dynamic = MetaField('strict')  # Do not auto map unknown fields and throw an error instead.

    class Serializer(DocumentSerializer):
        pass

    @property
    def uuid(self):
        return self.meta.id
