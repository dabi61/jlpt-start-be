"""
Views for Learning app.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UserUnitProgress,
    BookSet,
    BookSetUnit,
    BookSetUnitDetail,
)
from .serializers import (
    LessonSerializer,
    UnitSerializer,
    UnitWordDetailSerializer,
    UnitGrammarDetailSerializer,
    UnitKanjiDetailSerializer,
    UserUnitProgressSerializer,
    BookSetSerializer,
    BookSetUnitSerializer,
    BookSetUnitDetailSerializer,
)


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
        return queryset


@extend_schema_view(
    list=extend_schema(description="List all unit-word relationships"),
    retrieve=extend_schema(description="Get a specific unit-word relationship"),
    create=extend_schema(description="Create a new unit-word relationship"),
    update=extend_schema(description="Update a unit-word relationship"),
    partial_update=extend_schema(description="Partially update a unit-word relationship"),
    destroy=extend_schema(description="Delete a unit-word relationship"),
)
class UnitWordDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for UnitWordDetail model."""
    queryset = UnitWordDetail.objects.all()
    serializer_class = UnitWordDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'word_id']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset


@extend_schema_view(
    list=extend_schema(description="List all unit-grammar relationships"),
    retrieve=extend_schema(description="Get a specific unit-grammar relationship"),
    create=extend_schema(description="Create a new unit-grammar relationship"),
    update=extend_schema(description="Update a unit-grammar relationship"),
    partial_update=extend_schema(description="Partially update a unit-grammar relationship"),
    destroy=extend_schema(description="Delete a unit-grammar relationship"),
)
class UnitGrammarDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for UnitGrammarDetail model."""
    queryset = UnitGrammarDetail.objects.all()
    serializer_class = UnitGrammarDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'grammar_id']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset


@extend_schema_view(
    list=extend_schema(description="List all unit-kanji relationships"),
    retrieve=extend_schema(description="Get a specific unit-kanji relationship"),
    create=extend_schema(description="Create a new unit-kanji relationship"),
    update=extend_schema(description="Update a unit-kanji relationship"),
    partial_update=extend_schema(description="Partially update a unit-kanji relationship"),
    destroy=extend_schema(description="Delete a unit-kanji relationship"),
)
class UnitKanjiDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for UnitKanjiDetail model."""
    queryset = UnitKanjiDetail.objects.all()
    serializer_class = UnitKanjiDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'kanji_id']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset


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


@extend_schema_view(
    list=extend_schema(description="List all book sets"),
    retrieve=extend_schema(description="Get a specific book set"),
    create=extend_schema(description="Create a new book set"),
    update=extend_schema(description="Update a book set"),
    partial_update=extend_schema(description="Partially update a book set"),
    destroy=extend_schema(description="Delete a book set"),
)
class BookSetViewSet(viewsets.ModelViewSet):
    """ViewSet for BookSet model."""
    queryset = BookSet.objects.all()
    serializer_class = BookSetSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'level']
    ordering_fields = ['id', 'name', 'level', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


@extend_schema_view(
    list=extend_schema(description="List all book set units"),
    retrieve=extend_schema(description="Get a specific book set unit"),
    create=extend_schema(description="Create a new book set unit"),
    update=extend_schema(description="Update a book set unit"),
    partial_update=extend_schema(description="Partially update a book set unit"),
    destroy=extend_schema(description="Delete a book set unit"),
)
class BookSetUnitViewSet(viewsets.ModelViewSet):
    """ViewSet for BookSetUnit model."""
    queryset = BookSetUnit.objects.all()
    serializer_class = BookSetUnitSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'book_set_id', 'name', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        book_set_id = self.request.query_params.get('book_set_id')
        if book_set_id:
            queryset = queryset.filter(book_set_id=book_set_id)
        return queryset


@extend_schema_view(
    list=extend_schema(description="List all book set unit details"),
    retrieve=extend_schema(description="Get a specific book set unit detail"),
    create=extend_schema(description="Create a new book set unit detail"),
    update=extend_schema(description="Update a book set unit detail"),
    partial_update=extend_schema(description="Partially update a book set unit detail"),
    destroy=extend_schema(description="Delete a book set unit detail"),
)
class BookSetUnitDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for BookSetUnitDetail model."""
    queryset = BookSetUnitDetail.objects.all()
    serializer_class = BookSetUnitDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'word_id']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        word_id = self.request.query_params.get('word_id')
        if word_id:
            queryset = queryset.filter(word_id=word_id)
        return queryset
