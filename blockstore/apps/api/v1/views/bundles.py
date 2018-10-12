"""
Views for Bundles and BundleVersions.
"""

from rest_framework import viewsets, mixins
from rest_framework.generics import get_object_or_404

from blockstore.apps.bundles.models import Bundle, BundleVersion

from ...constants import UUID4_REGEX, VERSION_NUM_REGEX
from ..serializers.bundles import BundleSerializer, BundleVersionSerializer


class BundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bundle model.
    """

    lookup_field = 'uuid'
    lookup_url_kwarg = 'bundle_uuid'
    lookup_value_regex = UUID4_REGEX

    queryset = Bundle.objects.all()
    serializer_class = BundleSerializer


class BundleVersionViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for BundleVersion model.
    """

    lookup_fields = ('bundle__uuid', 'version_num')
    lookup_url_kwargs = ('bundle_uuid', 'version_num')
    lookup_value_regexes = (UUID4_REGEX, VERSION_NUM_REGEX)

    queryset = BundleVersion.objects.all()
    serializer_class = BundleVersionSerializer

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        filter_kwargs = {
            key: self.kwargs[value] for key, value in zip(self.lookup_fields, self.lookup_url_kwargs)
        }

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
