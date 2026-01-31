"""
Views for Kanji app.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Kanji
from .serializers import KanjiSerializer, KanjiListSerializer


class KanjiViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Kanji model.
    """
    queryset = Kanji.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['kanji', 'mean', 'on', 'kun']
    ordering_fields = ['kanji', 'level', 'stroke_count', 'created_at']
    ordering = ['level', 'kanji']

    def get_serializer_class(self):
        if self.action == 'list':
            return KanjiListSerializer
        return KanjiSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='level', description='Filter by JLPT level (1-5)', required=False, type=int),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List Kanji with optional level filtering."""
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
        description="Get Kanji statistics by level."
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get Kanji statistics by level."""
        from django.db.models import Count

        stats = Kanji.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')

        return Response({
            'total': Kanji.objects.count(),
            'by_level': list(stats)
        })

    @extend_schema(
        description="Get all examples for a specific kanji.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'kanji_id': {'type': 'integer', 'example': 1239},
                    'kanji': {'type': 'string', 'example': '襲'},
                    'example_count': {'type': 'integer', 'example': 12},
                    'examples': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'w': {'type': 'string', 'example': '襲う'},
                                'p': {'type': 'string', 'example': 'おそう'},
                                'h': {'type': 'string', 'example': 'TẬP'},
                                'm': {'type': 'string', 'example': 'công kích; tấn công'},
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def examples(self, request, pk=None):
        """Get all examples for a specific kanji."""
        kanji = self.get_object()
        examples = kanji.examples if isinstance(kanji.examples, list) else []
        return Response({
            'kanji_id': kanji.id,
            'kanji': kanji.kanji,
            'example_count': len(examples),
            'examples': examples
        })

    @extend_schema(
        description="Get component details for a specific kanji.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'kanji_id': {'type': 'integer', 'example': 1239},
                    'kanji': {'type': 'string', 'example': '襲'},
                    'comp': {'type': 'string', 'example': '龍衣'},
                    'stroke_count': {'type': 'integer', 'example': 22},
                    'component_count': {'type': 'integer', 'example': 2},
                    'compDetail': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'w': {'type': 'string', 'example': '龍'},
                                'h': {'type': 'string', 'example': 'LONG, SỦNG'},
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def components(self, request, pk=None):
        """Get component details for a specific kanji."""
        kanji = self.get_object()
        comp_detail = kanji.compDetail if isinstance(kanji.compDetail, list) else []
        return Response({
            'kanji_id': kanji.id,
            'kanji': kanji.kanji,
            'comp': kanji.comp,
            'stroke_count': kanji.stroke_count,
            'component_count': len(comp_detail),
            'compDetail': comp_detail
        })


