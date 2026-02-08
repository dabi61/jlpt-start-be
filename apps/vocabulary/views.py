"""
Views for Vocabulary app.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Word
from .serializers import WordSerializer, WordListSerializer, WordCreateSerializer


class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Word model.

    Endpoints:
    - GET /api/vocabulary/ - List words
    - POST /api/vocabulary/ - Create word
    - GET /api/vocabulary/{id}/ - Get word detail
    - PUT/PATCH /api/vocabulary/{id}/ - Update word
    - DELETE /api/vocabulary/{id}/ - Delete word
    - GET /api/vocabulary/by_level/?level=N5 - Filter by level
    """
    queryset = Word.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['j_word', 'phonetic', 'short_mean', 'han']
    ordering_fields = ['j_word', 'level', 'created_at']
    ordering = ['level', 'j_word']

    def get_serializer_class(self):
        if self.action == 'list':
            return WordListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return WordCreateSerializer
        return WordSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='level', description='Filter by JLPT level (N1-N5)', required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List words with optional level filtering."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level.upper())

        return queryset

    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get words filtered by JLPT level."""
        level = request.query_params.get('level', 'N5')
        words = self.get_queryset().filter(level=level.upper())
        page = self.paginate_queryset(words)

        if page is not None:
            serializer = WordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WordListSerializer(words, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get vocabulary counting statistics by level."
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get vocabulary statistics by level."""
        from django.db.models import Count

        stats = Word.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')

        return Response({
            'total': Word.objects.count(),
            'by_level': list(stats)
        })

    @extend_schema(
        description="Get all examples for a specific word.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'word_id': {'type': 'integer', 'example': 59227},
                    'j_word': {'type': 'string', 'example': '１０分'},
                    'example_count': {'type': 'integer', 'example': 3},
                    'examples': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 17812},
                                'content': {'type': 'string', 'example': '１０分休憩しよう。'},
                                'mean': {'type': 'string', 'example': 'Hãy nghỉ ngơi 10 phút.'},
                                'trans': {'type': 'string', 'example': '１０ふんきゅうけいしよう。'},
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def examples(self, request, pk=None):
        """Get all examples for a specific word."""
        from apps.examples.serializers import ExampleSerializer

        word = self.get_object()
        examples = word.get_example_objects()
        serializer = ExampleSerializer(examples, many=True)
        return Response({
            'word_id': word.id,
            'j_word': word.j_word,
            'example_count': examples.count(),
            'examples': serializer.data
        })

