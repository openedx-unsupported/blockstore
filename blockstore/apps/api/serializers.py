"""
Blockstore serializers
"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from ..core.models import Tag, Unit, Pathway


class TagSerializer(ModelSerializer):
    """Serialize the Tag model"""
    class Meta:
        model = Tag
        fields = '__all__'


class UnitSerializer(ModelSerializer):
    """Serialize the Unit model"""
    class Meta:
        model = Unit
        fields = '__all__'

    tags = SerializerMethodField()

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


class PathwaySerializer(ModelSerializer):
    """Serialize the Pathway model"""
    class Meta:
        model = Pathway
        fields = '__all__'

    units = UnitSerializer(read_only=True, many=True)
    tags = SerializerMethodField()

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]
