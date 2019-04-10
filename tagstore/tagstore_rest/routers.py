"""
Routers for Tagstore API.
"""

from rest_framework_nested import routers
from rest_framework.routers import Route


class EntityRouter(routers.DefaultRouter):
    """
    Custom routing for the Entity model.
    """
    routes = [
        Route(
            url=r'^{prefix}$',
            mapping={'get': 'list'},
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        Route(
            url=r'^{prefix}/(?P<entity_type>[^/.]+)/{lookup}$',
            mapping={'get': 'retrieve'},
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
        Route(
            url=r'^{prefix}/(?P<entity_type>[^/.]+)/{lookup}/tags/(?P<taxonomy_id>\d+)/(?P<tag_name>.*)$',
            mapping={'get': 'has_tag', 'post': 'add_tag', 'delete': 'remove_tag'},
            name='{basename}-tag-change',
            detail=True,
            initkwargs={'suffix': 'Tags'}
        ),
    ]
