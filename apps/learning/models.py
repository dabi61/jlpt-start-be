"""
Models for Learning app.
Manages lessons, units, and user progress tracking.
"""
from django.db import models
from django.utils import timezone


class Lesson(models.Model):
    """
    Model for Lessons (Bài học).
    Contains multiple Units.
    """
    lession_name = models.TextField(
        'lesson name',
        blank=True,
        null=True,
        help_text='Name of the lesson'
    )
    level = models.CharField(
        'JLPT level',
        max_length=5,
        blank=True,
        null=True,
        help_text='JLPT level (N5, N4, N3, N2, N1)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'lesson'
        verbose_name_plural = 'lessons'
        ordering = ['id']

    def __str__(self):
        return self.lession_name or f"Lesson {self.id}"


class Unit(models.Model):
    """
    Model for Units within a Lesson.
    Each unit can contain words, grammar points, and kanji.
    """
    unit_name = models.TextField(
        'unit name',
        blank=True,
        null=True,
        help_text='Name of the unit'
    )
    lession_id = models.TextField(
        'lesson id',
        blank=True,
        null=True,
        help_text='ID of the parent lesson'
    )
    total = models.TextField(
        'total items',
        blank=True,
        null=True,
        help_text='Total number of items in this unit'
    )
    unit_type = models.TextField(
        'unit type',
        blank=True,
        null=True,
        help_text='Type of unit (vocabulary, grammar, kanji, mixed)'
    )
    level = models.CharField(
        'JLPT level',
        max_length=5,
        blank=True,
        null=True,
        help_text='JLPT level (N5, N4, N3, N2, N1)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'unit'
        verbose_name_plural = 'units'
        ordering = ['id']

    def __str__(self):
        return self.unit_name or f"Unit {self.id}"


class UnitWordDetail(models.Model):
    """
    Junction table linking Units to Words.
    """
    unit_id = models.TextField(
        'unit id',
        blank=True,
        null=True,
        help_text='ID of the unit'
    )
    word_id = models.TextField(
        'word id',
        blank=True,
        null=True,
        help_text='ID of the word'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'unit word detail'
        verbose_name_plural = 'unit word details'
        ordering = ['id']

    def __str__(self):
        return f"Unit {self.unit_id} - Word {self.word_id}"


class UnitGrammarDetail(models.Model):
    """
    Junction table linking Units to Grammar points.
    """
    unit_id = models.TextField(
        'unit id',
        blank=True,
        null=True,
        help_text='ID of the unit'
    )
    grammar_id = models.TextField(
        'grammar id',
        blank=True,
        null=True,
        help_text='ID of the grammar point'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'unit grammar detail'
        verbose_name_plural = 'unit grammar details'
        ordering = ['id']

    def __str__(self):
        return f"Unit {self.unit_id} - Grammar {self.grammar_id}"


class UnitKanjiDetail(models.Model):
    """
    Junction table linking Units to Kanji.
    """
    unit_id = models.TextField(
        'unit id',
        blank=True,
        null=True,
        help_text='ID of the unit'
    )
    kanji_id = models.TextField(
        'kanji id',
        blank=True,
        null=True,
        help_text='ID of the kanji'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'unit kanji detail'
        verbose_name_plural = 'unit kanji details'
        ordering = ['id']

    def __str__(self):
        return f"Unit {self.unit_id} - Kanji {self.kanji_id}"


class UserUnitProgress(models.Model):
    """
    Tracks user progress for each unit.
    Links to Unit and Lesson for progress tracking per lesson.
    """
    unit_id = models.TextField(
        'unit id',
        blank=True,
        null=True,
        help_text='ID of the unit'
    )
    lession_id = models.TextField(
        'lesson id',
        blank=True,
        null=True,
        help_text='ID of the lesson (for easier querying by lesson)'
    )
    progress = models.TextField(
        'progress',
        blank=True,
        null=True,
        help_text='Progress value (e.g., percentage or status)'
    )
    completed_at = models.TextField(
        'completed at',
        blank=True,
        null=True,
        help_text='Completion timestamp'
    )
    user_id = models.TextField(
        'user id',
        blank=True,
        null=True,
        help_text='ID of the user'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'user unit progress'
        verbose_name_plural = 'user unit progresses'
        ordering = ['id']

    def __str__(self):
        return f"User {self.user_id} - Unit {self.unit_id}"


class UnitAnkiCard(models.Model):
    """
    Per-user spaced repetition state for one item inside one unit.
    """

    class ItemType(models.TextChoices):
        VOCABULARY = 'vocabulary', 'Vocabulary'
        GRAMMAR = 'grammar', 'Grammar'
        KANJI = 'kanji', 'Kanji'

    class CardState(models.TextChoices):
        NEW = 'new', 'New'
        LEARNING = 'learning', 'Learning'
        RELEARNING = 'relearning', 'Relearning'
        REVIEW = 'review', 'Review'

    unit_id = models.TextField(
        'unit id',
        db_index=True,
        help_text='ID of the unit'
    )
    user_id = models.TextField(
        'user id',
        db_index=True,
        help_text='ID of the user'
    )
    item_type = models.CharField(
        'item type',
        max_length=20,
        choices=ItemType.choices,
        help_text='Type of linked learning item'
    )
    item_id = models.TextField(
        'item id',
        help_text='ID of the linked vocabulary/grammar/kanji record'
    )
    state = models.CharField(
        'card state',
        max_length=20,
        choices=CardState.choices,
        default=CardState.NEW,
        db_index=True,
    )
    step_index = models.PositiveSmallIntegerField(
        'learning step index',
        default=0,
        help_text='Current learning or relearning step index'
    )
    interval_days = models.PositiveIntegerField(
        'interval (days)',
        default=0,
        help_text='Next review interval in days when card is in review state'
    )
    ease_factor = models.FloatField(
        'ease factor',
        default=2.5,
        help_text='SM-2 ease factor used to grow intervals'
    )
    reps = models.PositiveIntegerField(
        'review repetitions',
        default=0,
        help_text='Total number of times this card was answered'
    )
    lapses = models.PositiveIntegerField(
        'lapses',
        default=0,
        help_text='How many times a review card failed (Again)'
    )
    due_at = models.DateTimeField(
        'due at',
        default=timezone.now,
        db_index=True,
        help_text='When this card should appear again'
    )
    last_reviewed_at = models.DateTimeField(
        'last reviewed at',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'unit anki card'
        verbose_name_plural = 'unit anki cards'
        ordering = ['due_at', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['unit_id', 'user_id', 'item_type', 'item_id'],
                name='learning_unitankicard_unique_user_unit_item',
            ),
        ]
        indexes = [
            models.Index(fields=['user_id', 'unit_id', 'due_at']),
            models.Index(fields=['user_id', 'unit_id', 'state']),
        ]

    def __str__(self):
        return f"User {self.user_id} - Unit {self.unit_id} - {self.item_type}:{self.item_id}"


class UnitAnkiReviewLog(models.Model):
    """
    Audit trail for each review answer sent from the client.
    """

    class Rating(models.TextChoices):
        AGAIN = 'again', 'Again'
        HARD = 'hard', 'Hard'
        GOOD = 'good', 'Good'
        EASY = 'easy', 'Easy'

    card = models.ForeignKey(
        UnitAnkiCard,
        on_delete=models.CASCADE,
        related_name='review_logs',
        verbose_name='anki card',
    )
    rating = models.CharField(
        'rating',
        max_length=10,
        choices=Rating.choices,
    )
    previous_state = models.CharField(
        'previous state',
        max_length=20,
    )
    next_state = models.CharField(
        'next state',
        max_length=20,
    )
    previous_interval_days = models.PositiveIntegerField(
        'previous interval (days)',
        default=0,
    )
    next_interval_days = models.PositiveIntegerField(
        'next interval (days)',
        default=0,
    )
    previous_ease_factor = models.FloatField(
        'previous ease factor',
        default=2.5,
    )
    next_ease_factor = models.FloatField(
        'next ease factor',
        default=2.5,
    )
    response_time_ms = models.PositiveIntegerField(
        'response time (ms)',
        blank=True,
        null=True,
        help_text='Optional client-side answer time'
    )
    reviewed_at = models.DateTimeField(
        'reviewed at',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'unit anki review log'
        verbose_name_plural = 'unit anki review logs'
        ordering = ['-reviewed_at']

    def __str__(self):
        return f"Card {self.card_id} - {self.rating}"


