"""
Project pagination settings.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Default pagination with configurable page size via query params.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
