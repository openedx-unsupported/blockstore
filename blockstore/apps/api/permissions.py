"""
Blockstore API permissions
"""
from django.core.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from ..core.models import Pathway


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow authors of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Instance must have an attribute named `author`.
        return hasattr(obj, 'author') and obj.author == request.user


class IsOwnerOfPathway(IsOwnerOrReadOnly):
    """
    Object-level permission granted only to authors of the pathway indicated in the request data.
    """
    def has_permission(self, request, view):
        """Can add or delete units on own pathway."""
        if IsAuthenticated().has_permission(request, view):
            pathway_id = request.data['pathway']
            try:
                pathway = Pathway.objects.get(id=pathway_id)
            except (Pathway.DoesNotExist, ValidationError):
                return False
            return super().has_object_permission(request, view, pathway)
        return False
