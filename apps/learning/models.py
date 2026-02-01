"""
Models for Learning app.
Manages lessons, units, and user progress tracking.
"""
from django.db import models


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



