"""
Admin configuration for Learning app.
"""
from django.contrib import admin

from .models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UserUnitProgress,
    UnitAnkiCard,
    UnitAnkiReviewLog,
)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'lession_name', 'created_at', 'updated_at']
    search_fields = ['lession_name']
    ordering = ['id']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_name', 'lession_id', 'total', 'unit_type', 'created_at']
    search_fields = ['unit_name', 'lession_id']
    list_filter = ['unit_type']
    ordering = ['id']


@admin.register(UnitWordDetail)
class UnitWordDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_id', 'word_id', 'created_at']
    search_fields = ['unit_id', 'word_id']
    ordering = ['id']


@admin.register(UnitGrammarDetail)
class UnitGrammarDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_id', 'grammar_id', 'created_at']
    search_fields = ['unit_id', 'grammar_id']
    ordering = ['id']


@admin.register(UnitKanjiDetail)
class UnitKanjiDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_id', 'kanji_id', 'created_at']
    search_fields = ['unit_id', 'kanji_id']
    ordering = ['id']


@admin.register(UserUnitProgress)
class UserUnitProgressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'unit_id', 'lession_id', 'progress', 'completed_at', 'created_at']
    search_fields = ['user_id', 'unit_id', 'lession_id']
    list_filter = ['lession_id']
    ordering = ['id']


@admin.register(UnitAnkiCard)
class UnitAnkiCardAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_id', 'unit_id', 'item_type', 'item_id',
        'state', 'interval_days', 'ease_factor', 'due_at',
    ]
    search_fields = ['user_id', 'unit_id', 'item_id']
    list_filter = ['item_type', 'state']
    ordering = ['due_at', 'id']


@admin.register(UnitAnkiReviewLog)
class UnitAnkiReviewLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'card', 'rating', 'previous_state', 'next_state',
        'previous_interval_days', 'next_interval_days', 'reviewed_at',
    ]
    search_fields = ['card__user_id', 'card__unit_id', 'card__item_id']
    list_filter = ['rating', 'previous_state', 'next_state']
    ordering = ['-reviewed_at']


