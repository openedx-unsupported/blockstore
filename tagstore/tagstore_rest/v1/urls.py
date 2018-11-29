""" API v1 URLs for Tagstore. """

from django.conf.urls import url, include
from rest_framework_nested import routers as nested_routers

from ..routers import DefaultRouter
from .views.entities import EntityViewSet, EntityTagViewSet

root_router = DefaultRouter()

root_router.register(r'entities', EntityViewSet)

entities_nested_router = nested_routers.NestedDefaultRouter(root_router, r'entities', lookup='')
entities_nested_router.register(r'tags', EntityTagViewSet, base_name='entitytags')

urlpatterns = [
    url(r'^', include(root_router.urls)),
    url(r'^', include(entities_nested_router.urls)),
]
