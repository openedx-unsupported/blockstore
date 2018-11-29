'''
Views for Tags and Taxonomies.
'''

from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from tagstore.backends.tagstore_django.models import Entity, Tag

from ..serializers.entities import EntitySerializer, EntityTagSerializer


class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    ViewSet for Entity model.
    '''

    lookup_field = 'external_id'
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


class EntityTagViewSet(viewsets.ViewSet):
    '''
    ViewSet for Tag model.
    '''

    queryset = Tag.objects.all()
    serializer_class = EntityTagSerializer

    def _convert(self, tag: Tag) -> dict:
        '''
        Prepare the tag for serialization.
        '''
        return {
            'taxonomy_uid': tag.taxonomy.id,
            'taxonomy_name': tag.taxonomy.name,
            'tag': tag.name,
        }

    def list(self, request, external_id=None):
        '''
        Get a list of all tags belonging to an entity.

        These can be optionally filtered by `taxonomy` params.
        '''
        entity = get_object_or_404(Entity, external_id=external_id)
        taxonomies = request.GET.get('taxonomies', '').split(',')

        if taxonomies[0]:
            try:
                queryset = entity.tags.filter(taxonomy__in=taxonomies)
            except ValueError:
                queryset = entity.tags.filter(taxonomy__name__in=taxonomies)
        else:
            queryset = entity.tags.all()

        extracted = [self._convert(tag) for tag in queryset]
        serializer = EntityTagSerializer({'tags': extracted})
        return Response(serializer.data)
