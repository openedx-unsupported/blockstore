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


class UnitSerializer(ModelSerializer):
    """Serialize the Unit model"""
    class Meta:
        model = Unit
        fields = '__all__'

    tags = SerializerMethodField()

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]


class TagUnitsSerializer(ModelSerializer):
    """Serialize the Tag model and paginate its related units"""
    class Meta:
        model = Tag
        fields = '__all__'

    units = SerializerMethodField()

    def get_units(self, obj):
        """Fetch the tagged units."""
        # TODO: paginate units
        units = Unit.objects.filter(tags__in=[obj])
        return UnitSerializer(units, many=True).data


class PathwaySerializer(ModelSerializer):
    """Serialize the Pathway model"""
    class Meta:
        model = Pathway
        fields = '__all__'

    units = SerializerMethodField()

    def get_units(self, obj):
        """Fetch the pathway units, in sorted order."""
        # For some reason, DRF doesn't respect the ManyToManyField's through model ordering
        joins = PathwayUnit.objects.filter(pathway=obj)
        joins = joins.order_by('index', 'unit')
        joins = joins.prefetch_related('unit', 'unit__tags')
        return UnitSerializer((join.unit for join in joins), many=True).data


class UnitPathwaysSerializer(UnitSerializer):
    """Serialize the Unit model with related Pathways"""
    pathways = SerializerMethodField()

    def get_pathways(self, obj):
        """Fetch the pathways that contain the current unit."""
        # TODO add pagination
        joins = PathwayUnit.objects.filter(unit=obj)
        joins = joins.order_by('index', 'pathway')
        joins = joins.prefetch_related('pathway', 'pathway__units__tags')
        return PathwaySerializer((join.pathway for join in joins), many=True).data
