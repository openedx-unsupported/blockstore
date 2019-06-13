"""
Serializers for Draft (the Django Model) and StagedDraft (the repo primitive)

This is a bit unusual in that we have slightly different serializers for list
vs. detail, and an entirely different one for writes.
"""
import base64
import binascii

from django.core.files.base import ContentFile
from rest_framework import relations, serializers

from blockstore.apps.bundles.models import Bundle, Draft
from blockstore.apps.bundles.store import (
    DraftRepo, SnapshotRepo, is_safe_file_path
)


class DraftSerializer(serializers.ModelSerializer):
    """Serializer for Drafts, appropriate for list views. No files metadata."""
    class Meta:
        model = Draft
        queryset = Draft.objects.all().select_related('bundle')
        fields = ('uuid', 'url', 'bundle', 'bundle_uuid', 'name')

    url = relations.HyperlinkedIdentityField(
        lookup_field='uuid',
        view_name='api:v1:draft-detail',
    )

    bundle = relations.HyperlinkedRelatedField(
        lookup_field='uuid',
        lookup_url_kwarg='bundle_uuid',
        view_name='api:v1:bundle-detail',
        read_only=True,
    )

    bundle_uuid = relations.SlugRelatedField(
        source='bundle',
        slug_field='uuid',
        queryset=Bundle.objects.all(),
    )


class DraftWithFileDataSerializer(DraftSerializer):
    """
    DraftSerializer subclass that adds files metadata.

    This payload could become very large, so this serializer should not be used
    for list views.
    """
    class Meta:
        model = Draft
        queryset = Draft.objects.all()
        fields = DraftSerializer.Meta.fields + ('staged_draft',)

    class StagedDraftField(serializers.Field):
        """Read-only field for a StagedDraft."""

        def to_representation(self, value):
            """StagedDraft JSON serialization."""
            staged_draft = value
            draft_repo = DraftRepo(SnapshotRepo())
            if staged_draft.base_snapshot is None:
                base_snapshot_repr = None
            else:
                base_snapshot_repr = staged_draft.base_snapshot.hash_digest.hex()

            basic_info = {
                'base_snapshot': base_snapshot_repr,
                'created_at': staged_draft.created_at,
                'updated_at': staged_draft.updated_at,
            }
            basic_info['files'] = {
                path: {
                    "url": draft_repo.url(staged_draft, path),
                    "size": file_info.size,
                    "hash_digest": file_info.hash_digest.hex(),
                    "modified": path in staged_draft.files_to_overwrite
                }
                for path, file_info in staged_draft.files.items()
            }
            return basic_info

        def to_internal_value(self, _data):
            raise NotImplementedError()

    staged_draft = StagedDraftField()


class DraftFileUpdateSerializer(serializers.BaseSerializer):
    """Write-only serializer for Draft file updates."""
    # pylint: disable=abstract-method

    def to_internal_value(self, data):
        """
        Convert file names -> b64 strings into file names -> ContentFiles.

        `data` is a  dict of file names to base64 encoded data representations.
        """
        if 'files' not in data or not isinstance(data['files'], dict):
            raise serializers.ValidationError('Missing "files" dict')

        for file_name in data['files']:
            if not is_safe_file_path(file_name):
                raise serializers.ValidationError(u'"{}" is not a valid file name'.format(file_name))

        def _parse_file_data(file_path, b64_encoded_str):
            """Parse base64 encoded file data into ContentFile if valid."""
            # If the value is None, it means "delete this file".
            if b64_encoded_str is None:
                return None

            # Otherwise, return the base64 representation
            try:
                binary_file_data = base64.b64decode(b64_encoded_str)
            except binascii.Error as err:
                raise serializers.ValidationError(
                    u"Error decoding file {}: {} (check if it's base64 encoded?)".format(file_path, err)
                )
            return ContentFile(binary_file_data)

        # TODO: make sure they can't write outside the draft space
        return {
            file_path: _parse_file_data(file_path, file_data)
            for file_path, file_data in data['files'].items()
        }
