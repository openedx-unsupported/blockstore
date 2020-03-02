'''
Views for Tags and Taxonomies.
'''
import logging

from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from tagstore.backends.tagstore_django.models import (
    Entity,
    Tag,
    Taxonomy
)
from tagstore.backends.django import DjangoTagstore
from tagstore.models.taxonomy import TaxonomyId

from tagstore.constants import FREEFORM_TAXONOMY_UID

from ..serializers.entities import EntitySerializer, EntityTagSerializer

logger = logging.getLogger(__name__)


class EntityViewSet(viewsets.ViewSet):
    '''
    ViewSet for Entity model and its tags.
    '''

    queryset = Entity.objects.all()
    serializer_class = EntitySerializer

    def list(self, request, *args, **kwargs):
        '''
        Get a list of all entities.
        '''
        serializer = EntitySerializer(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, entity_type=None):
        '''
        Get a single entity.
        '''
        entity = get_object_or_404(Entity, external_id=pk, entity_type=entity_type)
        serializer = EntitySerializer(entity)
        return Response(serializer.data)

    def _convert(self, tag: Tag) -> dict:
        '''
        Prepare the tag for serialization.
        '''
        return {
            'taxonomy_uid': tag.taxonomy.id,
            'taxonomy_name': tag.taxonomy.name,
            'tag': tag.name,
        }

    def serialize_tags(self, entity, taxonomies=None):
        '''
        Serialize an entity's tags, optionally filtered by taxonomy.
        '''
        if taxonomies and taxonomies[0]:
            try:
                queryset = entity.tags.filter(taxonomy__in=taxonomies)
            except ValueError:
                queryset = entity.tags.filter(taxonomy__name__in=taxonomies)
        else:
            queryset = entity.tags.all()

        extracted = [self._convert(tag) for tag in queryset]
        return EntityTagSerializer({'tags': extracted})

    def tags(self, request, entity_type=None, pk=None):
        '''
        Get a list of all tags belonging to an entity.

        These can be optionally filtered by `taxonomy` params.
        '''
        entity = get_object_or_404(Entity, external_id=pk, entity_type=entity_type)
        taxonomies = request.GET.get('taxonomies', '').split(',')

        serializer = self.serialize_tags(entity, taxonomies)
        return Response(serializer.data)

    def update_tags(self, request, entity_type=None, pk=None):
        '''
        Update tags belonging to an entity.
        '''
        tagstore = DjangoTagstore()

        entity_obj = get_object_or_404(Entity, external_id=pk, entity_type=entity_type)
        freeform_obj, _ = Taxonomy.objects.get_or_create(id=FREEFORM_TAXONOMY_UID, name='FreeForm')
        freeform = TaxonomyId(freeform_obj.id)

        if not request.data.get('tags', ''):
            return Response(status=204)

        for tag in request.data['tags']:
            # a single free form tag
            if isinstance(tag, str):
                _tag = tagstore.get_tag_in_taxonomy(tag, freeform)
                if not _tag:
                    _tag = tagstore.add_tag_to_taxonomy(tag, freeform)
                tagstore.add_tag_to(_tag, entity_obj.as_tuple)

            # a tag within a taxonomy
            elif isinstance(tag, dict):
                taxonomy_uid = tag.get('taxonomy_uid', None)
                tag_name = tag.get('tag', None)
                tag_parent = tag.get('parent', None)

                if not taxonomy_uid or not tag_name:
                    continue

                tx_obj, _ = Taxonomy.objects.get_or_create(id=taxonomy_uid)

                tx = TaxonomyId(tx_obj.id)
                p = tagstore.get_tag_in_taxonomy(tag_parent, tx)
                _tag = tagstore.get_tag_in_taxonomy(tag_name, tx)
                if not _tag:
                    _tag = tagstore.add_tag_to_taxonomy(tag_name, tx, p)
                tagstore.add_tag_to(_tag, entity_obj.as_tuple)

        serializer = self.serialize_tags(entity_obj)
        return Response(serializer.data, status=201)
