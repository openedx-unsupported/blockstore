"""
Views for Bundles and BundleVersions.
"""

from rest_framework import viewsets
from rest_framework.generics import get_object_or_404

from blockstore.apps.bundles.models import Bundle, BundleVersion

from ...constants import SLUG_REGEX, VERSION_NUM_REGEX
from ..serializers.bundles import BundleSerializer, BundleVersionSerializer


class BundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Bundle model.
    """

    lookup_field = 'slug'
    lookup_url_kwarg = 'bundle_slug'
    lookup_value_regex = SLUG_REGEX

    queryset = Bundle.objects.all()
    serializer_class = BundleSerializer


class BundleVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for BundleVersion model.
    """

    lookup_fields = ('bundle__slug', 'version_num')
    lookup_url_kwargs = ('bundle_slug', 'version_num')
    lookup_value_regexes = (SLUG_REGEX, VERSION_NUM_REGEX)

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
