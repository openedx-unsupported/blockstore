"""
Root API URLs.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.urls import include, path

app_name = 'blockstore'

urlpatterns = [
    path('v1/', include('blockstore.apps.rest_api.v1.urls', namespace='v1')),
]
