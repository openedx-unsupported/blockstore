"""
Serializers for Snapshots.
"""

from django.core.files.storage import default_storage
from rest_framework import serializers
from expander import ExpanderSerializerMixin

from blockstore.apps.bundles.models import BundleVersion
from ... import relations


class FileHyperlinkedIdentityField(relations.HyperlinkedIdentityField):
    """
    A HyperlinkedIdentityField for a nested FileInfo resource.
    """

    def get_url(self, obj, view_name, request, format):  # pylint: disable=redefined-builtin
        request = self.context['request']
        return self.reverse(
            self.context.get('detail_view_name', view_name),
            kwargs={
                'path': obj.path,
                **request.parser_context['kwargs'],
            },
            request=request,
            format=format,
        )


class FileDataField(serializers.FileField):
    """
    A FileField for FileInfo data field whose representation is a link to the file.
    """

    def get_attribute(self, instance):
        # We pass the object instance onto `to_representation`, not just the field attribute.
        return instance

    def to_representation(self, value):
        request = self.context['request']
        data_location = "{}/data/{}".format(request.parser_context['kwargs']['bundle_uuid'], value.hash_digest.hex())
        return self.context['request'].build_absolute_uri(default_storage.url(data_location))


class FileInfoSerializer(serializers.Serializer):
    """
    Serializer for a FileInfo object.
    """
    # pylint: disable=abstract-method

    data = FileDataField()
    path = serializers.CharField()
    public = serializers.BooleanField(default=False)
    size = serializers.IntegerField(read_only=True)

    url = FileHyperlinkedIdentityField(
        lookup_field='path',
        lookup_url_kwarg='path',
        view_name='api:v1:bundlefile-detail',
    )


class ExpandedFileInfoField(serializers.SerializerMethodField):
    """
    Serializer field which expands the related BundleVersion files into a list of FileInfoSerializers.
    """
    # pylint: disable=abstract-method

    def __init__(self, view_name, *args, **kwargs):
        """
        Initialize the ExpandedFileInfoField.
        """
        assert view_name is not None, 'The `view_name` argument is required.'
        self.view_name = view_name

        # Ignore the context argument if passed from the ExpanderSerializerMixin
        kwargs.pop('context', None)

        super().__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        """
        Bind our `expand_files` method to the parent serializer's `get_<field>` attribute.

        This way, our method is called when the field is serialized.
        """
        super().bind(field_name, parent)
        setattr(self.parent, self.method_name, self.expand_files)

    def expand_files(self, instance):
        """
        Returns the expanded list of BundleVersion files.
        """
        view = self.context.get('view')
        request = self.context.get('request')
        file_info_serializer = FileInfoSerializer(
            self._get_files(instance),
            context={
                'detail_view_name': self.view_name,
                'request': request,
                'format': getattr(view, 'format_kwarg', None),
            },
            many=True
        )
        return file_info_serializer.data

    def _get_files(self, instance):
        """
        Returns the BundleVersion files associated with the given instance.
        """
        if isinstance(instance, BundleVersion):
            bundle_version = instance
        else:
            bundle_version = instance.get_bundle_version()

        return bundle_version.snapshot().files.values()


class SingleExpanderSerializerMixin(ExpanderSerializerMixin):
    """
    Allows configured fields to be expanded only if serializing a single object.
    """

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        Disable requests for expanded fields when serializing a list of objects.
        """
        kwargs['expanded_fields'] = 'none'
        return super().many_init(*args, **kwargs)
