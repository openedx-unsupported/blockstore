"""
Blockstore serializers
"""
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from ..core.models import Tag, Unit, Pathway, PathwayUnit


class TagSerializer(ModelSerializer):
    """Serialize the Tag model"""
    class Meta:
        model = Tag
        fields = '__all__'

    tags = SerializerMethodField()
    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


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

    units = SerializerMethodField()
    def get_units(self, obj):
        """Fetch the pathway units, in sorted order."""
        # For some reason, DRF doesn't respect the ManyToManyField's through model ordering
        units = PathwayUnit.objects.filter(pathway=obj).order_by('index', 'unit').prefetch_related('unit', 'unit__tags')
        return UnitSerializer((unit.unit for unit in units), many=True).data
