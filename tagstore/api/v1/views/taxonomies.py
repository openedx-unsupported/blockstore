"""
Viewset for Tags and Taxonomies.
"""
import logging

from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from blockstore.apps.api.schema import api_method
from tagstore.models import (
    Entity,
    EntityId,
    Tag,
    Taxonomy,
)
from tagstore.api.serializers import (
    EmptyObjectSerializer,
    TagSerializer,
    TaxonomySerializer,
)

logger = logging.getLogger(__name__)


class TaxonomyViewSet(viewsets.GenericViewSet):
    """
    ViewSet for a Taxonomy and the tags it contains.

    A Taxonomy is a set of tags, which may be either a flat collection of tags
    or a hierarchical tree of tags.
    """
    queryset = Taxonomy.objects.all()

    def get_serializer_class(self):
        """
        When creating a tag from the browseable API, show the correct form.
        Otherwise, show the form for creating a taxonomy.
        """
        if self.action.endswith('tag') or self.action.endswith('tags'):
            return TagSerializer
        return TaxonomySerializer

    @swagger_auto_schema(operation_id="get_taxonomies")
    def list(self, request):  # pylint: disable=unused-argument
        """
        Get a list of all taxonomies.
        """
        page = self.paginate_queryset(self.get_queryset())
        serializer = TaxonomySerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(operation_id="get_taxonomy")
    def retrieve(self, request, pk):  # pylint: disable=unused-argument
        """
        Get a specific taxonomy.
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        return Response(TaxonomySerializer(taxonomy).data)

    @swagger_auto_schema(operation_id="delete_taxonomy")
    def delete(self, request, pk):  # pylint: disable=unused-argument
        """
        Delete a specific taxonomy and all of its tags.
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        taxonomy.delete()
        return Response({})

    @swagger_auto_schema(operation_id="create_taxonomy")
    def create(self, request):
        """
        Create a new Taxonomy
        """
        serializer = TaxonomySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        owner = None
        if data["owner"] is not None:
            # Get/create the entity that owns this taxonomy, if any:
            owner = Entity.get(EntityId(
                entity_type=data["owner"]["entity_type"],
                external_id=data["owner"]["external_id"],
            ))

        taxonomy = Taxonomy.objects.create(
            name=data["name"],
            owner=owner,
        )
        return Response(TaxonomySerializer(taxonomy).data)

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(operation_id="get_taxonomy_tags")
    def tags(self, request, pk=None):  # pylint: disable=unused-argument
        """
        List the tags in this taxonomy.

        It guarantees that parent tags will be returned before their children.
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        tags_query = taxonomy.tags.order_by('path')
        page = self.paginate_queryset(tags_query)
        return self.get_paginated_response(TagSerializer(page, many=True).data)

    @action(detail=True, url_path=r'tags/(?P<tag_name>.+)')
    @api_method(TagSerializer(), operation_id="get_taxonomy_tag")
    def tag(self, request, pk, tag_name: str):  # pylint: disable=unused-argument
        """
        Get a specific tag in the taxonomy
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        return get_object_or_404(taxonomy.tags, name__iexact=tag_name)

    @tag.mapping.delete
    @api_method(EmptyObjectSerializer(), operation_id="delete_taxonomy_tag")
    def delete_tag(self, request, pk, tag_name: str):  # pylint: disable=unused-argument
        """
        Delete a tag
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        tag = get_object_or_404(taxonomy.tags, name__iexact=tag_name)
        tag.delete()
        return {}

    @tags.mapping.post
    @api_method(TagSerializer(), operation_id="add_taxonomy_tag", request_body=TagSerializer)
    def add_tag(self, request, pk):
        """
        Add a tag to the taxonomy, if it doesn't already exist
        """
        taxonomy = get_object_or_404(self.queryset, pk=pk)
        parent_tag = None
        tag_name = request.data['name']
        if 'parent' in request.data:
            parent_tag = get_object_or_404(taxonomy.tags, name__iexact=request.data['parent'])
        try:
            tag = taxonomy.add_tag(tag_name, parent_tag=parent_tag)
        except Tag.AlreadyExistsError:
            raise ValidationError("That tag exists elsewhere in the hierarchy.")
        return tag
