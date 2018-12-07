"""
Base Serializers for search.
"""

from rest_framework import serializers


class DocumentSerializer(serializers.Serializer):
    """
    Base Serializer for Documents.
    """

    field_set_serializers = None

    uuid = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Since we do not have the detail_view_name for the base class, need to add this dynamically.
        detail_view_name = kwargs.get('context', {}).get('detail_view_name', None)
        if detail_view_name:
            self.fields['url'] = serializers.HyperlinkedIdentityField(
                lookup_field='uuid',
                lookup_url_kwarg='uuid',
                view_name=detail_view_name,
            )

        # For each of the FieldSets associated with this Document, add the Serializer as a nested field.
        for (name, serializer) in self.field_set_serializers.items():
            self.fields[name] = serializer(required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class FieldSetSerializer(serializers.Serializer):
    """
    Base Serializer for FieldSets.

    Each FieldSet must have a Serializer which can be used to serialize and deserialize its fields.
    """

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
