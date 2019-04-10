"""
Serializers for Entities.
"""
from rest_framework import serializers

from tagstore.models import Entity


class TagSerializer(serializers.Serializer):
    """
    Basic serializer for serializing a tag
    """
    # pylint: disable=abstract-method
    taxonomy_id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField()
    path = serializers.CharField()


class EntitySerializer(serializers.ModelSerializer):
    """
    Serializer for the Entity model.
    """

    class Meta:
        model = Entity
        fields = (
            'entity_type',
            'external_id',
        )


class EntityDetailSerializer(EntitySerializer):
    """
    Serializer for the Entity model, including a list of tags
    """
    persisted = serializers.BooleanField(source='is_persisted', read_only=True)
    tags = serializers.SerializerMethodField()
    # ^ We don't use tags = serializers.TagSerializer(many=True, read_only=True)
    #   because it can't handle 'Entity' objects that aren't yet saved to the DB

    def get_tags(self, obj):
        """
        Support returning 'tags' relationship even if the Entity isn't saved
        to the database
        """
        if obj.pk:
            return TagSerializer(obj.tags.all(), many=True, read_only=True).data
        return []

    class Meta(EntitySerializer.Meta):
        depth = 1
        fields = EntitySerializer.Meta.fields + (
            'persisted',
            'tags',
        )
