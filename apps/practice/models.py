"""
Per-user JLPT practice state.

The N3/N4/N5 datasets are immutable question banks. User answers must not be stored
in those tables (e.g. N5QuestionItem.choose_answer) because that becomes global.

This app stores attempts and answers generically across levels (N1..N6) by
referencing dataset record IDs (exam_id, question_item_id) plus `level`.
"""

from django.conf import settings
from django.db import models


class PracticeAttempt(models.Model):
    class JLPTLevel(models.TextChoices):
        N6 = 'N6', 'Beginner'
        N5 = 'N5', 'N5 - Basic'
        N4 = 'N4', 'N4 - Elementary'
        N3 = 'N3', 'N3 - Intermediate'
        N2 = 'N2', 'N2 - Pre-Advanced'
        N1 = 'N1', 'N1 - Advanced'

    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        ABANDONED = 'ABANDONED', 'Abandoned'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_attempts',
    )
    level = models.CharField(max_length=2, choices=JLPTLevel.choices, db_index=True)
    exam_id = models.BigIntegerField(db_index=True)

    # Snapshots for easier querying/display (do not rely on joins to dataset tables).
    section_code = models.SlugField(max_length=50, blank=True, default='')
    subcategory_code = models.SlugField(max_length=80, blank=True, default='')
    exam_name = models.CharField(max_length=200, blank=True, default='')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True)

    total_items = models.PositiveIntegerField(default=0)
    answered_items = models.PositiveIntegerField(default=0)
    correct_items = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    submitted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'practice attempt'
        verbose_name_plural = 'practice attempts'
        ordering = ['-started_at', '-id']
        indexes = [
            models.Index(fields=['user', 'level', 'exam_id']),
            models.Index(fields=['user', 'status', 'started_at']),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} {self.level} exam={self.exam_id} ({self.status})"


class PracticeAnswer(models.Model):
    attempt = models.ForeignKey(
        PracticeAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question_item_id = models.BigIntegerField(db_index=True)

    selected_answer = models.IntegerField(blank=True, null=True)
    correct_answer = models.IntegerField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    response_time_ms = models.PositiveIntegerField(blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'practice answer'
        verbose_name_plural = 'practice answers'
        ordering = ['attempt_id', 'question_item_id', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question_item_id'],
                name='practice_answer_unique_attempt_item',
            ),
        ]
        indexes = [
            models.Index(fields=['attempt', 'updated_at']),
        ]

    def __str__(self) -> str:
        return f"attempt={self.attempt_id} item={self.question_item_id}"

