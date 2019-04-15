"""
Root API URLs.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.conf.urls import url, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

API_INFO = openapi.Info(
    title="Blockstore API",
    default_version='v1',
    description="REST API for Open edX Blockstore",
    license=openapi.License(name="AGPL"),
)

api_schema_view = get_schema_view(
   API_INFO,
   public=True,
   permission_classes=(permissions.AllowAny, ),
)

urlpatterns = [
    url(r'^v1/', include('blockstore.apps.api.v1.urls', namespace='v1')),
    # The API specification at /api.yaml
    url(r'^spec(?P<format>\.json|\.yaml)$', api_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # The browseable API documentation, using Swagger or Redoc:
    url(r'^docs/$', api_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', api_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
