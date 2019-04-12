""" API v1 URLs for Tagstore. """

from django.conf.urls import url, include

from ..routers import EntityRouter
from .views.entities import EntityViewSet
from .views.taxonomies import TaxonomyViewSet

root_router = EntityRouter(trailing_slash=False)

root_router.register(r'entities', EntityViewSet)
root_router.register(r'taxonomies', TaxonomyViewSet)

urlpatterns = [
    url(r'^', include(root_router.urls)),
]
