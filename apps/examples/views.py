"""
Views for Examples app.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Example
from .serializers import ExampleSerializer


class ExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Example model.
    """
    queryset = Example.objects.all()
    serializer_class = ExampleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'mean', 'trans']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
