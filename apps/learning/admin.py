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
    BookSet,
    BookSetUnit,
    BookSetUnitDetail,
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


@admin.register(BookSet)
class BookSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'level', 'total_word', 'version', 'created_at']
    search_fields = ['name', 'level']
    list_filter = ['level', 'name']
    ordering = ['id']


@admin.register(BookSetUnit)
class BookSetUnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'book_set_id', 'name', 'total_word', 'created_at']
    search_fields = ['name', 'book_set_id']
    list_filter = ['book_set_id']
    ordering = ['id']


@admin.register(BookSetUnitDetail)
class BookSetUnitDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_id', 'word_id', 'sub_word', 'created_at']
    search_fields = ['unit_id', 'word_id']
    list_filter = ['unit_id']
    ordering = ['id']
