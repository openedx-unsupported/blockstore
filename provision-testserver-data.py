#!/usr/bin/env python
"""
Set up some useful data so that edx-platform can use this temporary blockstore
instance while running tests.

See 'make testserver' in the Makefile for details.
"""
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

# Create a staff user so developers can log in and debug issues:
debug_user, _ = User.objects.get_or_create(
    username='staff',
    is_staff=True,
    is_superuser=True,
)
debug_user.set_password('edx')
debug_user.save()

# Create a service user for the edx-platform to use when authentcating
# and making API calls during test runs.
edxapp_user, _ = User.objects.get_or_create(username='edxapp')
Token.objects.get_or_create(user=edxapp_user, key='edxapp-test-key')
