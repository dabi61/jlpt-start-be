from __future__ import annotations

import re
from typing import Any

from django.apps import apps as django_apps
from rest_framework import serializers

from .models import PracticeAnswer, PracticeAttempt


_LEVEL_RE = re.compile(r'^N[1-6]$')


def normalize_level(value: str) -> str:
    value = (value or '').strip().upper()
    if not _LEVEL_RE.match(value):
        raise serializers.ValidationError('Invalid level. Expected one of: N1..N6.')
    return value


def get_dataset_models(level: str):
    """
    Resolve dataset models dynamically by convention:
      level=N3 -> app_label='n3', models N3Exam/N3QuestionItem.
    """
    level = normalize_level(level)
    app_label = level.lower()
    try:
        exam_model = django_apps.get_model(app_label, f'{level}Exam')
        item_model = django_apps.get_model(app_label, f'{level}QuestionItem')
    except LookupError as exc:
        raise serializers.ValidationError(f'Unsupported level: {level}.') from exc
    return exam_model, item_model


class PracticeAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeAttempt
        fields = [
            'id',
            'level',
            'exam_id',
            'section_code',
            'subcategory_code',
            'exam_name',
            'status',
            'total_items',
            'answered_items',
            'correct_items',
            'score',
            'duration_ms',
            'metadata',
            'started_at',
            'submitted_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'section_code',
            'subcategory_code',
            'exam_name',
            'status',
            'total_items',
            'answered_items',
            'correct_items',
            'score',
            'duration_ms',
            'started_at',
            'submitted_at',
            'updated_at',
        ]


class PracticeAttemptCreateSerializer(serializers.Serializer):
    level = serializers.CharField()
    exam_id = serializers.IntegerField(min_value=1)
    resume = serializers.BooleanField(required=False, default=True)
    metadata = serializers.DictField(required=False)

    def validate_level(self, value: str) -> str:
        return normalize_level(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        level = attrs['level']
        exam_id = int(attrs['exam_id'])
        exam_model, _ = get_dataset_models(level)
        try:
            exam = exam_model.objects.select_related('subcategory', 'subcategory__section').get(id=exam_id)
        except exam_model.DoesNotExist as exc:
            raise serializers.ValidationError({'exam_id': 'Exam not found.'}) from exc

        attrs['exam'] = exam
        return attrs

    def create(self, validated_data: dict[str, Any]) -> PracticeAttempt:
        # Used by the view to decide between HTTP 200 (resume) vs 201 (create).
        self._resumed = False

        request = self.context['request']
        user = request.user

        level = validated_data['level']
        exam_id = int(validated_data['exam_id'])
        exam = validated_data['exam']
        resume = bool(validated_data.get('resume', True))
        metadata = validated_data.get('metadata') or {}

        if resume:
            existing = PracticeAttempt.objects.filter(
                user=user,
                level=level,
                exam_id=exam_id,
                status=PracticeAttempt.Status.IN_PROGRESS,
            ).first()
            if existing:
                self._resumed = True
                # Best-effort sync snapshots.
                section = getattr(getattr(exam, 'subcategory', None), 'section', None)
                existing.section_code = getattr(section, 'code', '') or ''
                existing.subcategory_code = getattr(getattr(exam, 'subcategory', None), 'code', '') or ''
                existing.exam_name = getattr(exam, 'name', '') or existing.exam_name
                if metadata:
                    merged = dict(existing.metadata or {})
                    merged.update(metadata)
                    existing.metadata = merged
                existing.save(update_fields=['section_code', 'subcategory_code', 'exam_name', 'metadata', 'updated_at'])
                return existing

        section_code = ''
        subcategory_code = ''
        try:
            section_code = exam.subcategory.section.code  # type: ignore[attr-defined]
            subcategory_code = exam.subcategory.code  # type: ignore[attr-defined]
        except Exception:
            # Keep snapshots best-effort; dataset models should have these fields.
            pass

        return PracticeAttempt.objects.create(
            user=user,
            level=level,
            exam_id=exam_id,
            section_code=section_code,
            subcategory_code=subcategory_code,
            exam_name=str(getattr(exam, 'name', '') or ''),
            metadata=metadata,
        )


class PracticeAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeAnswer
        fields = [
            'id',
            'attempt',
            'question_item_id',
            'selected_answer',
            'correct_answer',
            'is_correct',
            'response_time_ms',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'attempt', 'correct_answer', 'is_correct']


class PracticeAnswerUpsertSerializer(serializers.Serializer):
    question_item_id = serializers.IntegerField(min_value=1)
    selected_answer = serializers.IntegerField(required=True)
    response_time_ms = serializers.IntegerField(min_value=0, required=False)
    metadata = serializers.DictField(required=False)


class PracticeAnswerBatchUpsertSerializer(serializers.Serializer):
    answers = PracticeAnswerUpsertSerializer(many=True)
