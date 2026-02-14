"""
Views for Examples app.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from core.pagination import StandardResultsSetPagination
from .models import Example
from .serializers import ExampleSerializer


class ExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Example model.
    """
    queryset = Example.objects.all()
    serializer_class = ExampleSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'mean', 'trans']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
