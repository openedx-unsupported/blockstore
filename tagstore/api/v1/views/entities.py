'''
Tagstore API Viewset for the "Entity" API
'''
import logging

from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from blockstore.apps.api.schema import api_method
from tagstore.models import (
    Entity, EntityId,
    Tag,
)
from tagstore.api.serializers import EntitySerializer, EntityDetailSerializer, TagSerializer, EmptyObjectSerializer

logger = logging.getLogger(__name__)


class EntityViewSet(viewsets.GenericViewSet):
    '''
    ViewSet for Entity model and its tags.

    An entity is any person, place, or thing that can be tagged.

    In general, it's not necessary to explicitly create Entity objects in
    Tagstore; they will be transparently created if needed when you apply the
    first tag to an Entity. Likewise, any Entity that has never been created nor
    assigned tags will still be shown to exist (with no tags), in order to
    provide a consistent API experience (because Entities represent objects in
    external systems, and Tagstore really has no idea about what entities do or
    do not exist.)
    '''
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer

    @swagger_auto_schema(auto_schema=None)  # Exclude from API Specification
    def list(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Listing entities is generally not going to be performant, so is not
        supported by this API. Since entities are so varied and represent
        objects that are managed by external systems, there are not many use
        cases for listing all entities. We keep this endpoint only to enable
        the DRF web API browser.

        In the future we may add a way to list a subset of entities that match
        some critieria.
        """
        # page = self.paginate_queryset(self.get_queryset())
        # serializer = EntitySerializer(page, many=True)
        # return self.get_paginated_response(serializer.data)
        return Response([])

    @api_method(EntityDetailSerializer())
    def retrieve_entity(self, request, pk=None, entity_type=None):  # pylint: disable=unused-argument
        '''
        Get a single entity. Never raises a 404, because Tagstore doesn't know
        which entities exist or not. If you want to know whether or not the
        entity is persisted in Tagstore's database, check the resulting
        "persisted" boolean field.
        '''
        try:
            entity = Entity.objects.get(external_id=pk, entity_type=entity_type)
        except Entity.DoesNotExist:
            entity = Entity(external_id=pk, entity_type=entity_type)
        return entity

    @api_method(TagSerializer(exclude_parent=True))
    def entity_has_tag(self, request, pk, entity_type, taxonomy_id, tag_name):  # pylint: disable=unused-argument
        """
        Does this entity have the given tag?
        Use this if you need to check if an entity has one specific tag, as it
        will be faster than loading the entity's entire tag list.
        Raises 404 if the tag does not exist.
        """
        try:
            entity = Entity.objects.get(external_id=pk, entity_type=entity_type)
        except Entity.DoesNotExist:
            raise NotFound("Entity has no tags")
        try:
            return entity.tags.get(taxonomy_id=taxonomy_id, name=tag_name)
        except Tag.DoesNotExist:
            raise NotFound("Entity does not have that tag")

    @api_method(TagSerializer(exclude_parent=True), request_body=no_body)
    def entity_add_tag(self, request, pk, entity_type, taxonomy_id, tag_name):  # pylint: disable=unused-argument
        """
        Add the given tag to the entity. The entity will be auto-created if it
        isn't yet tracked (persisted) in Tagstore's database.

        Only raises an error if the tag does not exist.
        TODO: Add an option to auto-create the tag.
        """
        try:
            tag = Tag.objects.get(taxonomy_id=taxonomy_id, name=tag_name)
        except Tag.DoesNotExist:
            raise NotFound("Tag does not exist")
        tag.add_to(EntityId(external_id=pk, entity_type=entity_type))
        return tag

    @api_method(EmptyObjectSerializer())
    def entity_remove_tag(self, request, pk, entity_type, taxonomy_id, tag_name):  # pylint: disable=unused-argument
        """
        Remove the given tag from the entity.

        Only raises an error if the tag does not exist.

        We do not provide an option to auto-delete the tag from the taxonomy if
        it's not applied to any other entities, because tags can also be removed
        from entities when entities are deleted, and we want consistent behavior
        in both cases.
        TODO: Add a "prune" API method for any taxonomy that deletes any unused
        tags.
        """
        try:
            tag = Tag.objects.get(taxonomy_id=taxonomy_id, name=tag_name)
        except Tag.DoesNotExist:
            raise NotFound("Tag does not exist")
        tag.remove_from(EntityId(external_id=pk, entity_type=entity_type))
        return {}
