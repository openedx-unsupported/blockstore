"""
Blockstore API views
"""
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import get_object_or_404

from ..serializers import (
    PathwaySerializer,
    TagSerializer,
    TagUnitsSerializer,
    UnitSerializer,
    UnitPathwaysSerializer,
    PathwayTagSerializer,
    PathwayUnitSerializer,
)
from ..permissions import IsOwnerOrReadOnly, IsOwnerOfPathway
from ...core.models import Tag, Unit, Pathway, PathwayTag


class PaginatedView(object):
    """
    Paginate the list views.
    """
    pagination_class = PageNumberPagination
    page_size = 10
    max_page_size = 100
    page_size_query_param = 'per_page'


class TagView(object):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagList(TagView, PaginatedView, ListAPIView):
    permission_classes = ()


class TagNew(TagView, CreateAPIView):
    permission_classes = (IsAuthenticated,)


class TagGetOrUpdate(TagView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    lookup_field = 'name'


class TagUnits(TagView, PaginatedView, RetrieveAPIView):
    serializer_class = TagUnitsSerializer
    permission_classes = ()
    lookup_field = 'name'


class UnitView(object):
    queryset = Unit.objects.prefetch_related('tags')
    serializer_class = UnitSerializer


class UnitList(UnitView, PaginatedView, ListAPIView):
    permission_classes = ()


class UnitNew(UnitView, CreateAPIView):
    permission_classes = (IsAuthenticated,)


class UnitGetOrUpdate(UnitView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwnerOrReadOnly,)


class UnitPathways(UnitView, PaginatedView, RetrieveAPIView):
    serializer_class = UnitPathwaysSerializer
    permission_classes = ()


class PathwayView(object):
    queryset = Pathway.objects.prefetch_related('units', 'units__tags')
    serializer_class = PathwaySerializer


class PathwayList(PathwayView, PaginatedView, ListAPIView):
    permission_classes = ()


class PathwayNew(PathwayView, CreateAPIView):
    permission_classes = (IsAuthenticated,)


class PathwayGetOrUpdate(PathwayView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwnerOrReadOnly,)


class PathwayUnitCreateOrDelete(CreateAPIView, DestroyAPIView):
    serializer_class = PathwayUnitSerializer
    permission_classes = (IsOwnerOfPathway,)


class PathwayTagCreateOrDelete(CreateAPIView, DestroyAPIView):
    serializer_class = PathwayTagSerializer
    permission_classes = (IsOwnerOfPathway,)
    queryset = PathwayTag.objects.all()

    def get_object(self):
        """Fetch pathway tag from pathway and tag uuid."""
        pathway_id = self.request.data.get('pathway')
        tag_id = self.request.data.get('tag')
        assert pathway_id and tag_id, (
            "Expected view %s to be called with 'pathway' and 'tag' "
            "in the request data" % self.__class__.__name__
        )
        return get_object_or_404(self.queryset, pathway=pathway_id, tag=tag_id)
