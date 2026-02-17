from __future__ import annotations

from collections import defaultdict

from django.db import transaction
from django.utils import timezone
from rest_framework import filters, serializers as drf_serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer

from core.pagination import StandardResultsSetPagination
from .models import PracticeAnswer, PracticeAttempt
from .serializers import (
    PracticeAnswerBatchUpsertSerializer,
    PracticeAnswerSerializer,
    PracticeAnswerUpsertSerializer,
    PracticeAttemptCreateSerializer,
    PracticeAttemptSerializer,
    get_dataset_models,
    normalize_level,
)


class PracticeAttemptViewSet(viewsets.ModelViewSet):
    queryset = PracticeAttempt.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['exam_name', 'section_code', 'subcategory_code', 'level', 'status']
    ordering_fields = ['started_at', 'submitted_at', 'updated_at', 'correct_items', 'score']
    ordering = ['-started_at', '-id']

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        level = self.request.query_params.get('level')
        if level:
            try:
                qs = qs.filter(level=normalize_level(level))
            except Exception:
                pass
        exam_id = self.request.query_params.get('exam_id')
        if exam_id:
            try:
                qs = qs.filter(exam_id=int(exam_id))
            except (TypeError, ValueError):
                pass
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=str(status_param).strip().upper())
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return PracticeAttemptCreateSerializer
        return PracticeAttemptSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='level', required=False, type=str, description='Filter by JLPT level (N1..N6).'),
            OpenApiParameter(name='exam_id', required=False, type=int, description='Filter by dataset exam id.'),
            OpenApiParameter(
                name='status',
                required=False,
                type=str,
                description='Filter by attempt status (IN_PROGRESS|SUBMITTED|ABANDONED).',
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=PracticeAttemptCreateSerializer, responses={200: PracticeAttemptSerializer, 201: PracticeAttemptSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()
        # If resume=True and an attempt existed, we return 200 for idempotency.
        status_code = status.HTTP_200_OK if getattr(serializer, '_resumed', False) else status.HTTP_201_CREATED
        return Response(PracticeAttemptSerializer(attempt).data, status=status_code)

    @extend_schema(methods=['GET'], responses={200: PracticeAnswerSerializer(many=True)})
    @extend_schema(
        methods=['POST'],
        request=inline_serializer(
            name='PracticeAnswersUpsertRequest',
            fields={
                # Single-item payload
                'question_item_id': drf_serializers.IntegerField(required=False),
                'selected_answer': drf_serializers.IntegerField(required=False),
                'response_time_ms': drf_serializers.IntegerField(required=False),
                'metadata': drf_serializers.DictField(required=False),
                # Batch payload
                'answers': PracticeAnswerUpsertSerializer(many=True, required=False),
            },
        ),
        responses={200: PracticeAnswerSerializer(many=True), 400: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['get', 'post'], pagination_class=None)
    def answers(self, request, pk=None):
        attempt = self.get_object()

        if request.method.lower() == 'get':
            qs = attempt.answers.order_by('question_item_id', 'id')
            return Response(PracticeAnswerSerializer(qs, many=True).data)

        payload = request.data or {}
        items = payload.get('answers')
        if items is None:
            single = PracticeAnswerUpsertSerializer(data=payload)
            single.is_valid(raise_exception=True)
            items = [single.validated_data]
        else:
            batch = PracticeAnswerBatchUpsertSerializer(data=payload)
            batch.is_valid(raise_exception=True)
            items = batch.validated_data['answers']

        _, item_model = get_dataset_models(attempt.level)

        saved: list[PracticeAnswer] = []
        with transaction.atomic():
            for row in items:
                question_item_id = int(row['question_item_id'])
                selected_answer = int(row['selected_answer'])
                response_time_ms = row.get('response_time_ms')
                metadata = row.get('metadata') or {}

                try:
                    item = item_model.objects.select_related('question', 'question__exam').get(id=question_item_id)
                except item_model.DoesNotExist:
                    return Response(
                        {'message': f'Question item not found: {question_item_id}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Ensure the item belongs to the attempt's exam.
                try:
                    item_exam_id = int(item.question.exam_id)  # type: ignore[attr-defined]
                except Exception:
                    item_exam_id = 0
                if item_exam_id != int(attempt.exam_id):
                    return Response(
                        {'message': f'Question item {question_item_id} does not belong to exam {attempt.exam_id}.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                correct_answer = getattr(item, 'correct_answer', None)
                is_correct = None if correct_answer in (None, '') else int(selected_answer) == int(correct_answer)

                answer, _ = PracticeAnswer.objects.update_or_create(
                    attempt=attempt,
                    question_item_id=question_item_id,
                    defaults={
                        'selected_answer': selected_answer,
                        'correct_answer': None if correct_answer in (None, '') else int(correct_answer),
                        'is_correct': is_correct,
                        'response_time_ms': int(response_time_ms) if response_time_ms is not None else None,
                        'metadata': metadata,
                    },
                )
                saved.append(answer)

            # Update attempt progress counters (fast enough for typical attempt sizes).
            attempt.answered_items = PracticeAnswer.objects.filter(attempt=attempt).exclude(selected_answer__isnull=True).count()
            attempt.save(update_fields=['answered_items', 'updated_at'])

        return Response(PracticeAnswerSerializer(saved, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: PracticeAttemptSerializer, 400: OpenApiTypes.OBJECT})
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attempt = self.get_object()

        if attempt.status != PracticeAttempt.Status.IN_PROGRESS:
            return Response({'message': 'Attempt is not in progress.'}, status=status.HTTP_400_BAD_REQUEST)

        _, item_model = get_dataset_models(attempt.level)

        total_items = item_model.objects.filter(question__exam_id=attempt.exam_id).count()
        answered_items = PracticeAnswer.objects.filter(attempt=attempt).exclude(selected_answer__isnull=True).count()
        correct_items = PracticeAnswer.objects.filter(attempt=attempt, is_correct=True).count()

        now = timezone.now()
        duration_ms = max(0, int((now - attempt.started_at).total_seconds() * 1000))

        attempt.status = PracticeAttempt.Status.SUBMITTED
        attempt.submitted_at = now
        attempt.total_items = int(total_items)
        attempt.answered_items = int(answered_items)
        attempt.correct_items = int(correct_items)
        attempt.score = float(correct_items)
        attempt.duration_ms = duration_ms
        attempt.save(
            update_fields=[
                'status',
                'submitted_at',
                'total_items',
                'answered_items',
                'correct_items',
                'score',
                'duration_ms',
                'updated_at',
            ]
        )

        return Response(PracticeAttemptSerializer(attempt).data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: PracticeAttemptSerializer, 400: OpenApiTypes.OBJECT})
    @action(detail=True, methods=['post'])
    def abandon(self, request, pk=None):
        attempt = self.get_object()
        if attempt.status == PracticeAttempt.Status.SUBMITTED:
            return Response({'message': 'Attempt already submitted.'}, status=status.HTTP_400_BAD_REQUEST)
        attempt.status = PracticeAttempt.Status.ABANDONED
        attempt.save(update_fields=['status', 'updated_at'])
        return Response(PracticeAttemptSerializer(attempt).data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='level', required=False, type=str, description='Optional level filter (N1..N6).'),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'], pagination_class=None)
    def progress(self, request):
        """
        Summary progress for the current user.

        Optional query params:
          - level=N3 to get per-exam aggregates.
        """
        user = request.user
        level = request.query_params.get('level')
        qs = PracticeAttempt.objects.filter(user=user)

        if level:
            level = normalize_level(level)
            qs = qs.filter(level=level)
            # Per-exam aggregates (best score, attempts count, last submitted).
            per_exam: dict[int, dict] = defaultdict(lambda: {
                'exam_id': 0,
                'exam_name': '',
                'attempts': 0,
                'best_score': 0.0,
                'best_correct_items': 0,
                'best_total_items': 0,
                'last_submitted_at': None,
            })
            for attempt in qs.order_by('-submitted_at', '-started_at'):
                slot = per_exam[int(attempt.exam_id)]
                slot['exam_id'] = int(attempt.exam_id)
                slot['exam_name'] = attempt.exam_name
                slot['attempts'] += 1
                if attempt.status == PracticeAttempt.Status.SUBMITTED:
                    if float(attempt.score) > float(slot['best_score']):
                        slot['best_score'] = float(attempt.score)
                        slot['best_correct_items'] = int(attempt.correct_items)
                        slot['best_total_items'] = int(attempt.total_items)
                    if slot['last_submitted_at'] is None:
                        slot['last_submitted_at'] = attempt.submitted_at
            results = sorted(per_exam.values(), key=lambda x: (x['last_submitted_at'] is None, x['exam_id']))
            return Response({'level': level, 'results': results}, status=status.HTTP_200_OK)

        # Global per-level summary.
        by_level: dict[str, dict] = {}
        for attempt in qs.order_by('-updated_at'):
            slot = by_level.setdefault(attempt.level, {
                'level': attempt.level,
                'attempts': 0,
                'submitted': 0,
                'in_progress': 0,
                'abandoned': 0,
                'last_activity': None,
            })
            slot['attempts'] += 1
            if attempt.status == PracticeAttempt.Status.SUBMITTED:
                slot['submitted'] += 1
            elif attempt.status == PracticeAttempt.Status.ABANDONED:
                slot['abandoned'] += 1
            else:
                slot['in_progress'] += 1
            if slot['last_activity'] is None:
                slot['last_activity'] = attempt.updated_at

        return Response({'results': sorted(by_level.values(), key=lambda x: x['level'])}, status=status.HTTP_200_OK)
