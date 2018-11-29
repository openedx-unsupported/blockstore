""" API v1 URLs. """

from django.conf.urls import url, include
from rest_framework_nested import routers as nested_routers

from ..routers import DefaultRouter
from .views.bundles import BundleViewSet, BundleVersionViewSet
from .views.collections import CollectionViewSet
from .views.snapshots import BundleFileReadOnlyViewSet, BundleFileViewSet

root_router = DefaultRouter()

root_router.register(r'bundles', BundleViewSet)
root_router.register(r'bundle_versions', BundleVersionViewSet)
root_router.register(r'collections', CollectionViewSet)

bundles_nested_router = nested_routers.NestedDefaultRouter(root_router, r'bundles', lookup='')
bundles_nested_router.register(r'files', BundleFileViewSet, base_name='bundlefile')

bundle_versions_nested_router = nested_routers.NestedDefaultRouter(root_router, r'bundle_versions', lookup='')
bundle_versions_nested_router.register(r'files', BundleFileReadOnlyViewSet, base_name='bundleversionfile')

urlpatterns = [
    url(r'^', include(root_router.urls)),
    url(r'^', include(bundles_nested_router.urls)),
    url(r'^', include(bundle_versions_nested_router.urls)),
]
