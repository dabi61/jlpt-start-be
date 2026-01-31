"""
Views for Grammar app.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Grammar
from .serializers import GrammarSerializer, GrammarListSerializer, GrammarCreateSerializer


class GrammarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grammar model.
    """
    queryset = Grammar.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'mean', 'structure', 'about']
    ordering_fields = ['title', 'level', 'created_at']
    ordering = ['level', 'title']

    def get_serializer_class(self):
        if self.action == 'list':
            return GrammarListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return GrammarCreateSerializer
        return GrammarSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='level', description='Filter by JLPT level (1-5)', required=False, type=int),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List grammar points with optional level filtering."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by level
        level = self.request.query_params.get('level')
        if level:
            try:
                queryset = queryset.filter(level=int(level))
            except ValueError:
                pass

        return queryset

    @extend_schema(
        description="Get grammar statistics by level."
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get grammar statistics by level."""
        from django.db.models import Count

        stats = Grammar.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')

        return Response({
            'total': Grammar.objects.count(),
            'by_level': list(stats)
        })

    @extend_schema(
        description="Get all examples for a specific grammar point.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'grammar_id': {'type': 'integer', 'example': 2663},
                    'title': {'type': 'string', 'example': '１～たりとも～ない'},
                    'example_count': {'type': 'integer', 'example': 5},
                    'examples': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'example': {'type': 'string', 'example': '一瞬たりとも無駄にしない'},
                                'mean': {'type': 'string', 'example': 'Không lãng phí một khoảnh khắc nào'},
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def examples(self, request, pk=None):
        """Get all examples for a specific grammar point."""
        grammar = self.get_object()
        return Response({
            'grammar_id': grammar.id,
            'title': grammar.title,
            'example_count': grammar.example_count,
            'examples': grammar.get_examples_list()
        })

    @extend_schema(
        description="Get all synonyms/related grammar for a specific grammar point.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'grammar_id': {'type': 'integer', 'example': 2663},
                    'title': {'type': 'string', 'example': '１～たりとも～ない'},
                    'synonym_count': {'type': 'integer', 'example': 2},
                    'synonyms': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'example': {'type': 'string', 'example': '～も～ない'},
                                'mean': {'type': 'string', 'example': 'Không một cái nào'},
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def synonyms(self, request, pk=None):
        """Get all synonyms for a specific grammar point."""
        grammar = self.get_object()
        return Response({
            'grammar_id': grammar.id,
            'title': grammar.title,
            'synonym_count': len(grammar.get_synonyms_list()),
            'synonyms': grammar.get_synonyms_list()
        })


