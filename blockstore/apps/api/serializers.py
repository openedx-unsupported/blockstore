"""
Blockstore serializers
"""
from uuid import UUID
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ListSerializer

from ..core.models import Tag, Unit, Pathway, PathwayUnit, PathwayTag


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
        extra_fields = ['tags']


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

    tags = TagSerializer(many=True, read_only=False)
    units = UnitSerializer(many=True, read_only=False)

    def to_internal_value(self, data):
        """Convert any provided unit UUIDs to Units."""
        internal_value = super().to_internal_value(data)
        for (field, cls) in (
            ('units', Unit),
            ('tags', Tag),
        ):
            obj_ids = data.getlist(field, [])
            objs = cls.objects.filter(id__in=(UUID('{%s}' % id) for id in obj_ids))
            internal_value[field] = list(objs.all())
        return internal_value

    def _add_tags(self, pathway, tags):
        """Create associated pathway tags if provided."""
        for tag in tags:
            PathwayTag.objects.create(pathway=pathway, tag=tag)

    def _add_units(self, pathway, units):
        """Create associated pathway units if provided."""
        for unit in units:
            # TODO: preserve sort order
            PathwayUnit.objects.create(pathway=pathway, unit=unit)

    def create(self, validated_data):
        """Create pathway with given units, if any."""
        tags = validated_data.pop('tags')
        units = validated_data.pop('units')
        pathway = Pathway.objects.create(**validated_data)
        self._add_tags(pathway, tags)
        self._add_units(pathway, units)
        return pathway


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


class PathwayUnitSerializer(ModelSerializer):
    """Serialize the PathwayUnit model"""
    class Meta:
        model = PathwayUnit
        fields = '__all__'


class PathwayTagSerializer(ModelSerializer):
    """Serialize the PathwayTag model"""
    class Meta:
        model = PathwayTag
        fields = ['pathway', 'tag']
