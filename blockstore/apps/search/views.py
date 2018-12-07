"""
Views for search app.
"""
from .core.viewsets import DocumentViewSet
from .documents import BlockDocument


class BlockDocumentsViewSet(DocumentViewSet):
    """
    ViewSet for documents in the Blocks index.
    """

    document_class = BlockDocument
    serializer_class = BlockDocument.Serializer

    detail_view_name = 'api:v1:index-blocks-detail'
