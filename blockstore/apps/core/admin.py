""" Admin configuration for core models. """

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

import blockstore.apps.core.models as core_models


@admin.register(core_models.User)
class CustomUserAdmin(UserAdmin):
    """ Admin configuration for the custom User model. """
    list_display = ('username', 'email', 'full_name', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(core_models.Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for the Tag model."""
    pass


@admin.register(core_models.Unit)
class UnitAdmin(admin.ModelAdmin):
    """Admin configuration for the Unit model."""
    pass


class PathwayUnitInline(admin.TabularInline):
    model = core_models.PathwayUnit
    extra = 10  # how many rows to show


@admin.register(core_models.Pathway)
class PathwayAdmin(admin.ModelAdmin):
    """Admin configuration for the Pathway model."""
    inlines = (PathwayUnitInline,)


@admin.register(core_models.PathwayUnit)
class PathwayUnitAdmin(admin.ModelAdmin):
    """Admin configuration for the PathwayUnit model."""
    pass
