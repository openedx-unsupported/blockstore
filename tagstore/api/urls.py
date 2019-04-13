"""
Root API URLs for Tagstore.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.conf.urls import url, include

urlpatterns = [
    url(r'^api/v1/', include('tagstore.api.v1.urls', namespace='apiv1')),
]
