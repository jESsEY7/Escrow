"""
Custom pagination classes for the Escrow Platform.
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for list views."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        from rest_framework.response import Response
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class LargeResultsPagination(PageNumberPagination):
    """Pagination for larger datasets."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsPagination(PageNumberPagination):
    """Pagination for smaller datasets or mobile views."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class AuditLogPagination(CursorPagination):
    """Cursor-based pagination for audit logs (for performance with large datasets)."""
    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'


class TransactionPagination(PageNumberPagination):
    """Pagination for transaction history."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        from rest_framework.response import Response
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'summary': getattr(self, 'summary', None)
        })
