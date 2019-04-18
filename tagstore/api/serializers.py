"""
Serializers for Entities.
"""
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from tagstore.models import Taxonomy


class TagSerializer(serializers.Serializer):
    """
    Basic serializer for serializing a tag
    """
    # pylint: disable=abstract-method
    taxonomy_id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(help_text="Display name of this tag; also its identifier within the taxonomy.")
    path = serializers.CharField(read_only=True, help_text=("""
        'path' is provided for use in
        implementing searching by tag. It provides the following guarantees:
        (1) 'path' is globally unique.
        (2) any child tag's path string starts with its parent's tag's path.
    """))


class TagWithHierarchySerializer(TagSerializer):
    """
    Serializer for tags that also includes hierarchy information.
    """
    # pylint: disable=abstract-method
    parent = serializers.CharField(allow_null=True, allow_blank=False, default=None, source='parent_tag_name')


class EntitySerializer(serializers.Serializer):
    """
    Serializer for the Entity model.
    """
    # pylint: disable=abstract-method
    entity_type = serializers.CharField()
    external_id = serializers.CharField()


class EntityDetailSerializer(EntitySerializer):
    """
    Serializer for the Entity model, including a list of tags
    """
    # pylint: disable=abstract-method
    persisted = serializers.BooleanField(source='is_persisted', read_only=True)
    tags = serializers.SerializerMethodField()
    # ^ We don't use tags = serializers.TagSerializer(many=True, read_only=True)
    #   because it can't handle 'Entity' objects that aren't yet saved to the DB

    @swagger_serializer_method(serializer_or_field=TagSerializer(many=True))
    def get_tags(self, obj):
        """
        The list of tags that this entity has applied.
        """
        # Support returning 'tags' relationship even if the Entity isn't saved
        # to the database
        if obj.pk:
            return TagSerializer(obj.tags.all(), many=True, read_only=True).data
        return []


class TaxonomySerializer(serializers.ModelSerializer):
    """
    Serializer for the Taxonomy model.
    """
    id = serializers.IntegerField(read_only=True)
    owner = EntitySerializer(allow_null=True, default=None)

    class Meta:
        model = Taxonomy
        depth = 1
        fields = (
            'id',
            'name',
            'owner',
        )


class EmptyObjectSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    pass
