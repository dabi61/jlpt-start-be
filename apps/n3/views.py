"""ViewSets for N3 practice APIs."""
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.pagination import StandardResultsSetPagination
from .models import (
    N3Section,
    N3Subcategory,
    N3Exam,
    N3Question,
    N3QuestionItem,
    N3MediaAsset,
)
from .serializers import (
    N3SectionSerializer,
    N3SubcategorySerializer,
    N3ExamSerializer,
    N3QuestionListSerializer,
    N3QuestionSerializer,
    N3QuestionItemSerializer,
    N3MediaAssetSerializer,
)


class N3SectionViewSet(viewsets.ModelViewSet):
    queryset = N3Section.objects.all()
    serializer_class = N3SectionSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['sort_order', 'name', 'updated_at']
    ordering = ['sort_order', 'name']


class N3SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = N3Subcategory.objects.select_related('section').all()
    serializer_class = N3SubcategorySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'source_key', 'section__name', 'section__code']
    ordering_fields = ['sort_order', 'name', 'updated_at']
    ordering = ['section__sort_order', 'sort_order', 'name']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='section', description='Filter by section id', required=False, type=int),
            OpenApiParameter(name='section_code', description='Filter by section code', required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        section = self.request.query_params.get('section')
        if section:
            queryset = queryset.filter(section_id=section)

        section_code = self.request.query_params.get('section_code')
        if section_code:
            queryset = queryset.filter(section__code=section_code)

        return queryset


class N3ExamViewSet(viewsets.ModelViewSet):
    queryset = N3Exam.objects.select_related('subcategory', 'subcategory__section').all()
    serializer_class = N3ExamSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'source_file', 'source_kind', 'subcategory__name']
    ordering_fields = ['name', 'question_count', 'time_limit_seconds', 'updated_at']
    ordering = ['subcategory__sort_order', 'name']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='section', description='Filter by section id', required=False, type=int),
            OpenApiParameter(name='section_code', description='Filter by section code', required=False, type=str),
            OpenApiParameter(name='subcategory', description='Filter by subcategory id', required=False, type=int),
            OpenApiParameter(name='subcategory_code', description='Filter by subcategory code', required=False, type=str),
            OpenApiParameter(name='is_active', description='Filter by active state', required=False, type=bool),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        section = self.request.query_params.get('section')
        if section:
            queryset = queryset.filter(subcategory__section_id=section)

        section_code = self.request.query_params.get('section_code')
        if section_code:
            queryset = queryset.filter(subcategory__section__code=section_code)

        subcategory = self.request.query_params.get('subcategory')
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)

        subcategory_code = self.request.query_params.get('subcategory_code')
        if subcategory_code:
            queryset = queryset.filter(subcategory__code=subcategory_code)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            truthy = {'1', 'true', 'yes'}
            falsy = {'0', 'false', 'no'}
            lowered = str(is_active).strip().lower()
            if lowered in truthy:
                queryset = queryset.filter(is_active=True)
            elif lowered in falsy:
                queryset = queryset.filter(is_active=False)

        return queryset

    @extend_schema(responses={200: N3QuestionListSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        exam = self.get_object()
        queryset = exam.questions.order_by('display_order', 'id')
        page = self.paginate_queryset(queryset)
        serializer = N3QuestionListSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class N3QuestionViewSet(viewsets.ModelViewSet):
    queryset = N3Question.objects.select_related('exam', 'exam__subcategory', 'exam__subcategory__section').all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'kind', 'source_id', 'exam__name']
    ordering_fields = ['display_order', 'source_id', 'score', 'updated_at']
    ordering = ['exam', 'display_order']

    def get_serializer_class(self):
        if self.action == 'list':
            return N3QuestionListSerializer
        return N3QuestionSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='section', description='Filter by section id', required=False, type=int),
            OpenApiParameter(name='section_code', description='Filter by section code', required=False, type=str),
            OpenApiParameter(name='subcategory', description='Filter by subcategory id', required=False, type=int),
            OpenApiParameter(name='subcategory_code', description='Filter by subcategory code', required=False, type=str),
            OpenApiParameter(name='exam', description='Filter by exam id', required=False, type=int),
            OpenApiParameter(name='kind', description='Filter by kind', required=False, type=str),
            OpenApiParameter(name='source_id', description='Filter by source id', required=False, type=int),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        section = self.request.query_params.get('section')
        if section:
            queryset = queryset.filter(exam__subcategory__section_id=section)

        section_code = self.request.query_params.get('section_code')
        if section_code:
            queryset = queryset.filter(exam__subcategory__section__code=section_code)

        subcategory = self.request.query_params.get('subcategory')
        if subcategory:
            queryset = queryset.filter(exam__subcategory_id=subcategory)

        subcategory_code = self.request.query_params.get('subcategory_code')
        if subcategory_code:
            queryset = queryset.filter(exam__subcategory__code=subcategory_code)

        exam = self.request.query_params.get('exam')
        if exam:
            queryset = queryset.filter(exam_id=exam)

        kind = self.request.query_params.get('kind')
        if kind:
            queryset = queryset.filter(kind__iexact=kind.strip())

        source_id = self.request.query_params.get('source_id')
        if source_id:
            queryset = queryset.filter(source_id=source_id)

        return queryset

    @extend_schema(responses={200: N3QuestionItemSerializer(many=True)})
    @action(detail=True, methods=['get'], pagination_class=None)
    def items(self, request, pk=None):
        question = self.get_object()
        queryset = question.items.order_by('item_order', 'id')
        serializer = N3QuestionItemSerializer(queryset, many=True)
        return Response(serializer.data)


class N3QuestionItemViewSet(viewsets.ModelViewSet):
    queryset = N3QuestionItem.objects.select_related(
        'question', 'question__exam', 'question__exam__subcategory', 'question__exam__subcategory__section'
    ).all()
    serializer_class = N3QuestionItemSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['question_text', 'question__title']
    ordering_fields = ['item_order', 'correct_answer', 'updated_at']
    ordering = ['question', 'item_order']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='question', description='Filter by question id', required=False, type=int),
            OpenApiParameter(name='exam', description='Filter by exam id', required=False, type=int),
            OpenApiParameter(name='subcategory', description='Filter by subcategory id', required=False, type=int),
            OpenApiParameter(name='section', description='Filter by section id', required=False, type=int),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        question = self.request.query_params.get('question')
        if question:
            queryset = queryset.filter(question_id=question)

        exam = self.request.query_params.get('exam')
        if exam:
            queryset = queryset.filter(question__exam_id=exam)

        subcategory = self.request.query_params.get('subcategory')
        if subcategory:
            queryset = queryset.filter(question__exam__subcategory_id=subcategory)

        section = self.request.query_params.get('section')
        if section:
            queryset = queryset.filter(question__exam__subcategory__section_id=section)

        return queryset


class N3MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = N3MediaAsset.objects.all()
    serializer_class = N3MediaAssetSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['source_basename', 'source_path', 'source_url', 'r2_key', 'public_url']
    ordering_fields = ['created_at', 'updated_at', 'media_type', 'source_type']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='media_type', description='Filter by media type', required=False, type=str),
            OpenApiParameter(name='source_type', description='Filter by source type', required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        media_type = self.request.query_params.get('media_type')
        if media_type:
            queryset = queryset.filter(media_type=media_type.upper())

        source_type = self.request.query_params.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type=source_type.upper())

        return queryset
