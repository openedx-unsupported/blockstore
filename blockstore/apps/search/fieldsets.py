"""
FieldSets for search app.
"""

from elasticsearch_dsl import (
    Keyword,
    InnerDoc,
    Integer,
    Text,
)

from rest_framework import serializers

from .core.fieldsets import FieldSet
from .core.serializers import FieldSetSerializer


class EntityFieldSet(FieldSet):
    """
    FieldSet for core data of the entity.
    """

    name = 'entity'

    class Document(InnerDoc):

        # Since external identifiers of different types of entities may conflict, they should not be stored in the
        # document id field which needs to be unique. Store them as (type, id) in these instead.
        type = Keyword()
        id = Keyword()

    class Serializer(FieldSetSerializer):

        type = serializers.CharField()
        id = serializers.CharField()


class SummaryFieldSet(FieldSet):
    """
    FieldSet for summary data of the entity.
    """

    name = 'summary'

    class Document(InnerDoc):

        title = Text()
        description = Text()
        image = Text(index=False)

    class Serializer(FieldSetSerializer):

        title = serializers.CharField(allow_null=True, required=False)
        description = serializers.CharField(allow_null=True, required=False)
        image = serializers.URLField(allow_null=True, required=False)


class OwnernershipFieldSet(FieldSet):
    """
    FieldSet for ownership data of the entity.
    """

    name = 'ownership'

    class Document(InnerDoc):

        org_id = Keyword()

    class Serializer(FieldSetSerializer):

        org_id = serializers.CharField(allow_null=True, required=False)


class AuthorshipFieldSet(FieldSet):
    """
    FieldSet for authorship data of the entity.
    """

    name = 'authorship'

    class Document(InnerDoc):

        author_ids = Keyword(multi=True)

    class Serializer(FieldSetSerializer):

        author_ids = serializers.ListField(child=serializers.CharField(), required=False)


class TagsFieldSet(FieldSet):
    """
    FieldSet for tags associated with the entity.
    """
    name = 'tags'

    class Document(InnerDoc):

        paths = Keyword(multi=True)  # Materialized path.

    class Serializer(FieldSetSerializer):

        paths = serializers.ListField(child=serializers.CharField(), required=False)


class AnalyticsFieldSet(FieldSet):
    """
    FieldSet for analytics data.
    """

    name = 'analytics'

    class Document(InnerDoc):

        favorites = Integer()
        remixes = Integer()
        views = Integer()

    class Serializer(FieldSetSerializer):

        favorites = serializers.IntegerField(allow_null=True, required=False)
        remixes = serializers.IntegerField(allow_null=True, required=False)
        views = serializers.IntegerField(allow_null=True, required=False)
