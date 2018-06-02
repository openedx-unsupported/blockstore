"""
Blockstore serializers
"""
from uuid import UUID
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ListSerializer

from ..core.models import Tag, Unit, Pathway, PathwayUnit


class TagListSerializer(ListSerializer):
    """Serialize a list of Tags to a simple list of names"""
    class Meta:
        model = Tag
        fields = 'name'
    field_name = 'name'

    def update(self, instance, validated_data):
        """TODO: allow units to update their tag lists."""
        return super().update(instance, validated_data)


class TagSerializer(ModelSerializer):
    """Serialize the Tag model"""
    class Meta:
        model = Tag
        fields = '__all__'
        list_serializer_class = TagListSerializer


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

    # Tags are inferred from the units and so cannot be updated
    tags = TagSerializer(many=True, read_only=True)
    units = UnitSerializer(many=True, read_only=False)

    def to_internal_value(self, data):
        """Convert any provided unit UUIDs to Units."""
        internal_value = super().to_internal_value(data)
        unit_ids = data.getlist('units', [])
        units = Unit.objects.filter(id__in=(UUID('{%s}' % unit_id) for unit_id in unit_ids))
        internal_value['units'] = [unit for unit in units.all()]
        return internal_value

    def _add_units(self, pathway, units):
        """Create associated pathway units if provided."""
        for unit in units:
            PathwayUnit.objects.create(pathway=pathway, unit=unit)
        return pathway

    def create(self, validated_data):
        """Create pathway with given units, if any."""
        units = validated_data.pop('units')
        pathway = Pathway.objects.create(**validated_data)
        return self._add_units(pathway, units)


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
