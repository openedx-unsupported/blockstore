"""
Views for Snapshots.
"""

from django import http
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from blockstore.apps.bundles.store import BundleDataStore, BundleSnapshot
from blockstore.apps.bundles.models import BundleVersion

from ...constants import FILE_PATH_REGEX
from ..serializers.snapshots import FileInfoSerializer


class BundleFileReadOnlyViewSet(viewsets.ViewSet):
    """
    Read only ViewSet for files in a BundleVersion.
    """

    detail_view_name = 'api:v1:bundleversionfile-detail'

    lookup_field = 'path'
    lookup_value_regex = FILE_PATH_REGEX

    serializer_class = FileInfoSerializer

    def get_serializer_context(self):
        return {
            'detail_view_name': self.detail_view_name,
            'format': self.format_kwarg,
            'request': self.request,
        }

    def get_bundle_version(self, bundle_uuid, version_num=None):
        """ Get the bundle version. """

        filter_kwargs = {
            'bundle__uuid': bundle_uuid
        }
        if version_num:
            filter_kwargs['version_num'] = version_num

        try:
            return BundleVersion.objects.filter(**filter_kwargs).order_by('-version_num').first()
        except BundleVersion.DoesNotExist:
            pass
        return None

    def get_bundle_version_or_404(self, bundle_uuid, version_num=None):
        bundle_version = self.get_bundle_version(bundle_uuid, version_num)
        if bundle_version:
            return bundle_version
        raise http.Http404

    def list(self, _request, bundle_uuid, version_num=None):
        """ Retrieve all files in a bundle. """
        snapshot = self.get_bundle_version_or_404(bundle_uuid, version_num).snapshot()
        file_info_serializer = FileInfoSerializer(
            snapshot.files.values(),
            context=self.get_serializer_context(),
            many=True
        )
        return Response(file_info_serializer.data)

    def retrieve(self, _request, bundle_uuid, path, version_num=None):
        """ Retrieve details for a file in a bundle. """
        snapshot = self.get_bundle_version_or_404(bundle_uuid, version_num).snapshot()
        file = snapshot.files.get(path, None)
        if file:
            file_info_serializer = FileInfoSerializer(
                file,
                context=self.get_serializer_context(),
            )
            return Response(file_info_serializer.data)
        raise http.Http404


class BundleFileViewSet(BundleFileReadOnlyViewSet):
    """
    ViewSet for files in the most recent BundleVersion of a Bundle.
    """

    detail_view_name = 'api:v1:bundlefile-detail'

    def create(self, request, bundle_uuid, version_num=None):
        """ Add file to a bundle. """
        serializer = FileInfoSerializer(data=request.data)
        if serializer.is_valid():
            bundle_version = self.get_bundle_version(bundle_uuid, version_num)

            if bundle_version:
                snapshot = bundle_version.snapshot()
            else:
                snapshot = BundleSnapshot.create(bundle_uuid, {})

            store = BundleDataStore()
            snapshot = store.snapshot_by_adding_path(snapshot, **serializer.validated_data)

            response_serializer = FileInfoSerializer(
                snapshot.files[serializer.validated_data['path']],  # pylint: disable=unsubscriptable-object
                context=self.get_serializer_context(),
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, _request, bundle_uuid, version_num=None, path=None):
        """ Delete files from a bundle. """
        snapshot = self.get_bundle_version_or_404(bundle_uuid, version_num).snapshot()
        store = BundleDataStore()
        store.snapshot_by_removing_path(snapshot, path)
        return Response(status=status.HTTP_204_NO_CONTENT)
