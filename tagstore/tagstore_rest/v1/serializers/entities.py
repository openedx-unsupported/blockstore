"""
Serializers for Entities.
"""

from rest_framework import serializers
from tagstore.backends.tagstore_django.models import Entity


class EntitySerializer(serializers.ModelSerializer):
    """
    Serializer for the Entity model.
    """

    class Meta:

        model = Entity

        fields = (
            'id',
            'entity_type',
            'external_id',
        )


class TagByTaxonomySerializer(serializers.Serializer):
    """
    Serializer for the Tag model by Taxonomy.
    """
    # pylint: disable=abstract-method

    taxonomy_uid = serializers.IntegerField()
    taxonomy_name = serializers.CharField()
    tag = serializers.CharField()


class EntityTagSerializer(serializers.Serializer):
    """
    Serializer for the Tag model by Entity.
    """
    # pylint: disable=abstract-method

    tags = TagByTaxonomySerializer(many=True, required=False)
