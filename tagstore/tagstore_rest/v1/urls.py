""" API v1 URLs for Tagstore. """

from django.conf.urls import url, include

from ..routers import EntityRouter
from .views.entities import EntityViewSet

root_router = EntityRouter()

root_router.register(r'entities', EntityViewSet)

urlpatterns = [
    url(r'^', include(root_router.urls)),
]
