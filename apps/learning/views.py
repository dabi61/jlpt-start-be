"""
Views for Learning app.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UserUnitProgress,
)
from .serializers import (
    LessonSerializer,
    UnitSerializer,

    UserUnitProgressSerializer,
)

# Import serializers from other apps for unit detail
from apps.vocabulary.models import Word
from apps.vocabulary.serializers import WordSerializer
from apps.grammar.models import Grammar
from apps.grammar.serializers import GrammarSerializer
from apps.kanjis.models import Kanji
from apps.kanjis.serializers import KanjiSerializer


@extend_schema_view(
    list=extend_schema(description="List all lessons"),
    retrieve=extend_schema(description="Get a specific lesson"),
    create=extend_schema(description="Create a new lesson"),
    update=extend_schema(description="Update a lesson"),
    partial_update=extend_schema(description="Partially update a lesson"),
    destroy=extend_schema(description="Delete a lesson"),
)
class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for Lesson model."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lession_name']
    ordering_fields = ['id', 'lession_name', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    @extend_schema(
        description="Get all units of a lesson with summary counts",
        parameters=[
            OpenApiParameter(
                name='unit_type',
                description='Filter by unit type (vocabulary, grammar, kanji)',
                required=False,
                type=str
            ),
        ],
    )
    @action(detail=True, methods=['get'], url_path='units')
    def units(self, request, pk=None):
        """Get all units of a lesson with summary."""
        lesson = self.get_object()
        units = Unit.objects.filter(lession_id=str(lesson.id)).order_by('id')

        # Apply unit_type filter
        unit_type = request.query_params.get('unit_type')
        if unit_type:
            units = units.filter(unit_type=unit_type)

        # Calculate summary from all units (not filtered)
        all_units = Unit.objects.filter(lession_id=str(lesson.id))
        summary = {
            'total_units': all_units.count(),
            'vocabulary_units': all_units.filter(unit_type='vocabulary').count(),
            'grammar_units': all_units.filter(unit_type='grammar').count(),
            'kanji_units': all_units.filter(unit_type='kanji').count(),
        }

        return Response({
            'lesson': LessonSerializer(lesson).data,
            'summary': summary,
            'units': UnitSerializer(units, many=True).data
        })


@extend_schema_view(
    list=extend_schema(description="List all units"),
    retrieve=extend_schema(description="Get a specific unit"),
    create=extend_schema(description="Create a new unit"),
    update=extend_schema(description="Update a unit"),
    partial_update=extend_schema(description="Partially update a unit"),
    destroy=extend_schema(description="Delete a unit"),
)
class UnitViewSet(viewsets.ModelViewSet):
    """ViewSet for Unit model."""
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['unit_name', 'lession_id', 'unit_type']
    ordering_fields = ['id', 'unit_name', 'lession_id', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        lession_id = self.request.query_params.get('lession_id')
        if lession_id:
            queryset = queryset.filter(lession_id=lession_id)
        unit_type = self.request.query_params.get('unit_type')
        if unit_type:
            queryset = queryset.filter(unit_type=unit_type)
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    @extend_schema(
        description="Get unit detail with full content (words, grammar, or kanji)"
    )
    @action(detail=True, methods=['get'], url_path='detail')
    def detail_content(self, request, pk=None):
        """Get unit detail with full content based on unit type."""
        unit = self.get_object()
        items = []

        if unit.unit_type == 'vocabulary':
            # Get word IDs from junction table
            word_ids = list(UnitWordDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('word_id', flat=True))
            # Convert to integers and fetch words
            int_ids = [int(w) for w in word_ids if w and w.isdigit()]
            words = Word.objects.filter(id__in=int_ids).order_by('id')
            items = WordSerializer(words, many=True).data

        elif unit.unit_type == 'grammar':
            # Get grammar IDs from junction table
            grammar_ids = list(UnitGrammarDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('grammar_id', flat=True))
            # Convert to integers and fetch grammar
            int_ids = [int(g) for g in grammar_ids if g and g.isdigit()]
            grammars = Grammar.objects.filter(id__in=int_ids).order_by('id')
            items = GrammarSerializer(grammars, many=True).data

        elif unit.unit_type == 'kanji':
            # Get kanji IDs from junction table
            kanji_ids = list(UnitKanjiDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('kanji_id', flat=True))
            # Convert to integers and fetch kanji
            int_ids = [int(k) for k in kanji_ids if k and k.isdigit()]
            kanjis = Kanji.objects.filter(id__in=int_ids).order_by('id')
            items = KanjiSerializer(kanjis, many=True).data

        return Response({
            'unit': UnitSerializer(unit).data,
            'items': items
        })





@extend_schema_view(
    list=extend_schema(description="List all user unit progress records"),
    retrieve=extend_schema(description="Get a specific user unit progress"),
    create=extend_schema(description="Create a new user unit progress"),
    update=extend_schema(description="Update a user unit progress"),
    partial_update=extend_schema(description="Partially update a user unit progress"),
    destroy=extend_schema(description="Delete a user unit progress"),
)
class UserUnitProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for UserUnitProgress model."""
    queryset = UserUnitProgress.objects.all()
    serializer_class = UserUnitProgressSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'lession_id', 'user_id', 'progress']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        lession_id = self.request.query_params.get('lession_id')
        if lession_id:
            queryset = queryset.filter(lession_id=lession_id)
        return queryset



