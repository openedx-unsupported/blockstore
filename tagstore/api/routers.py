"""
Routers for Tagstore API.
"""

from rest_framework_nested import routers
from rest_framework.routers import Route, DynamicRoute


class EntityRouter(routers.DefaultRouter):
    """
    Custom routing for the Entity model.
    """
    routes = [
        Route(
            url=r'^{prefix}$',
            mapping={'get': 'list', 'post': 'create'},
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        Route(
            url=r'^{prefix}/{lookup}$',
            mapping={'get': 'retrieve', 'delete': 'delete'},
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
        Route(
            url=r'^{prefix}/(?P<entity_type>[^/.]+)/(?P<external_id>[^/.]+)$',
            mapping={'get': 'retrieve_entity'},
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Detail'}
        ),
        Route(
            url=r'^{prefix}/(?P<entity_type>[^/.]+)/(?P<external_id>[^/.]+)/tags/(?P<taxonomy_id>\d+)/(?P<name>.*)$',
            mapping={'get': 'entity_has_tag', 'post': 'entity_add_tag', 'delete': 'entity_remove_tag'},
            name='{basename}-tag-change',
            detail=True,
            initkwargs={'suffix': 'Tags'}
        ),
        # We must include DynamicRoute to allow routes defined by the @action
        # decorator to work, e.g. TaxonomyViewSet.tags
        DynamicRoute(
            url=r'^{prefix}/{lookup}/{url_path}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={}
        )
    ]
