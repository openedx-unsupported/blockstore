"""Blockstore URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
"""

import os

from auth_backends.urls import auth_urlpatterns
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework_swagger.views import get_swagger_view

from blockstore.apps.core import views as core_views

admin.autodiscover()

urlpatterns = auth_urlpatterns + [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('blockstore.apps.api.urls', namespace='api')),
    url(r'^api-docs/', get_swagger_view(title='blockstore API')),
    # Use the same auth views for all logins, including those originating from the browseable API.
    url(r'^api-auth/', include(auth_urlpatterns, namespace='rest_framework')),
    url(r'^auto_auth/$', core_views.AutoAuth.as_view(), name='auto_auth'),
    url(r'^health/$', core_views.health, name='health'),
]

if settings.DEBUG and os.environ.get('ENABLE_DJANGO_TOOLBAR', False):  # pragma: no cover
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
