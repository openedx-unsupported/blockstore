"""
edX standard pagination.

This is copied from edx-drf-extentions, since it's just a few lines of code,
we're not using any other extensions in that package, and we need to maintain
strict API stability. Also, the default page size and max page size are adjusted
for Blockstore.

Original:
https://github.com/edx/edx-drf-extensions/blob/master/edx_rest_framework_extensions/paginators.py
"""
from rest_framework import pagination
from rest_framework.response import Response


class DefaultPagination(pagination.PageNumberPagination):
    """
    Default paginator for edX APIs.
    """
    page_size_query_param = "page_size"
    page_size = 50
    max_page_size = 1000

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'start': (self.page.number - 1) * self.get_page_size(self.request),
            'results': data,
        })
