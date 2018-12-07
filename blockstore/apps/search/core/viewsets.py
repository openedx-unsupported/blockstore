"""
Base ViewSets for search.
"""

from django import http

from elasticsearch import exceptions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .documents import Document


class DocumentViewSet(viewsets.ViewSet):
    """
    Base ViewSet for searching and modifying documents in an ElasticSearch Index.
    """

    document_class = Document
    serializer_class = Document.Serializer
    lookup_field = 'uuid'

    page_size = 10
    max_page_size = 100

    def get_document_or_404(self, uuid):
        try:
            return self.document_class.get(id=uuid)
        except exceptions.NotFoundError:
            raise http.Http404

    def get_serializer_class(self):
        return self.document_class.Serializer

    def get_serializer_context(self):
        return {
            'detail_view_name': self.detail_view_name,
            'document_class': self.document_class,
            'format': self.format_kwarg,
            'request': self.request,
            'view': self,
        }

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def serialize_search_response(self, response):
        """
        Serialize ElasticSearch search response.
        """
        results_serializer = self.get_serializer(response.hits, many=True)
        response_data = response.to_dict()
        total_results = response_data['hits'].get('total', 0)
        response_data.pop('hits', None)
        aggregations = response_data.pop('aggregations', {})

        return {
            'count': total_results,
            'results': results_serializer.data,
            'aggregations': aggregations,
            'es': response_data,
        }

    def list(self, request):
        """
        View to GET documents list.
        """
        return self.search(request)

    def retrieve(self, _request, uuid):
        """
        View to GET a document.
        """
        document = self.get_document_or_404(uuid)
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    def create(self, request):
        """
        View to POST a new document.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = self.document_class(**serializer.validated_data)
        document.save()
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, uuid):
        """
        View to PATCH a document.
        """
        document = self.get_document_or_404(uuid)
        serializer = self.get_serializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        document.update(**serializer.validated_data)
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, _request, uuid):
        """
        View to DELETE a document.
        """
        document = self.get_document_or_404(uuid)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def search(self, _request):
        """
        View to search the documents.

        This does not do much right now. We can add a simplified version of search with query parameters if needed.
        """
        # TODO: We can add a last_updated field to show the most recently updated documents first.
        search = self.document_class.search().sort('-_doc').extra(from_=0, size=self.page_size)
        response = search.execute()
        return Response(self.serialize_search_response(response))

    @search.mapping.post
    def post_search(self, request):
        """
        View to search the documents with ElasticSearch Query DSL.
        """
        search = self.document_class.search().update_from_dict(request.data)
        response = search.execute()
        return Response(self.serialize_search_response(response))
