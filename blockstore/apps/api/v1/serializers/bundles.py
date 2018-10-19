"""
Serializers for Bundles and BundleVersions.
"""

from rest_framework import serializers
from expander import ExpanderSerializerMixin

from blockstore.apps.bundles.models import Bundle, BundleVersion, Collection
from ... import relations
from .snapshots import ExpandedFileInfoField


class BundleSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for the Bundle model.
    """

    class Meta:

        model = Bundle

        fields = (
            'collection',
            'description',
            'files',
            'slug',
            'title',
            'url',
            'uuid',
            'versions',
        )
        expandable_fields = {
            'files': (ExpandedFileInfoField, (), dict(
                view_name='api:v1:bundlefile-detail',
            ))
        }

    collection = relations.HyperlinkedRelatedField(
        lookup_field='uuid',
        lookup_url_kwarg='uuid',
        queryset=Collection.objects.all(),
        view_name='api:v1:collection-detail',
    )

    files = relations.HyperlinkedIdentityField(
        lookup_field='uuid',
        lookup_url_kwarg='bundle_uuid',
        view_name='api:v1:bundlefile-list',
    )

    url = relations.HyperlinkedIdentityField(
        lookup_field='uuid',
        lookup_url_kwarg='bundle_uuid',
        view_name='api:v1:bundle-detail',
    )

    versions = relations.HyperlinkedRelatedField(
        lookup_fields=['bundle__uuid', 'version_num'],
        lookup_url_kwargs=['bundle_uuid', 'version_num'],
        many=True,
        read_only=True,
        view_name='api:v1:bundleversion-detail',
    )


class BundleVersionSerializer(ExpanderSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for the BundleVersion model.
    """

    class Meta:

        model = BundleVersion

        fields = (
            'bundle',
            'change_description',
            'files',
            'url',
            'version_num',
        )
        expandable_fields = {
            'files': (ExpandedFileInfoField, (), dict(
                view_name='api:v1:bundleversionfile-detail',
            ))
        }

    bundle = relations.HyperlinkedRelatedField(
        lookup_field='uuid',
        lookup_url_kwarg='bundle_uuid',
        read_only=True,
        view_name='api:v1:bundle-detail',
    )

    files = relations.HyperlinkedIdentityField(
        lookup_fields=['bundle__uuid', 'version_num'],
        lookup_url_kwargs=['bundle_uuid', 'version_num'],
        view_name='api:v1:bundleversionfile-list',
    )

    url = relations.HyperlinkedIdentityField(
        lookup_fields=['bundle__uuid', 'version_num'],
        lookup_url_kwargs=['bundle_uuid', 'version_num'],
        view_name='api:v1:bundleversion-detail',
    )
