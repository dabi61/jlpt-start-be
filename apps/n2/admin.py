from django.contrib import admin

from .models import (
    N2Section,
    N2Subcategory,
    N2Exam,
    N2Question,
    N2QuestionItem,
    N2MediaAsset,
)


@admin.register(N2Section)
class N2SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'sort_order', 'updated_at')
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'name')


@admin.register(N2Subcategory)
class N2SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'section', 'code', 'source_key', 'sort_order', 'updated_at')
    list_filter = ('section',)
    search_fields = ('name', 'code', 'source_key')
    ordering = ('section__sort_order', 'sort_order', 'name')


@admin.register(N2Exam)
class N2ExamAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'subcategory', 'source_kind', 'question_count', 'time_limit_seconds', 'is_active', 'updated_at'
    )
    list_filter = ('subcategory__section', 'subcategory', 'is_active')
    search_fields = ('name', 'slug', 'source_file', 'source_kind')
    ordering = ('subcategory__sort_order', 'name')


@admin.register(N2Question)
class N2QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'source_id', 'display_order', 'kind', 'jlpt_level', 'score', 'updated_at')
    list_filter = ('exam__subcategory__section', 'exam__subcategory', 'exam', 'kind', 'jlpt_level')
    search_fields = ('title', 'kind', 'source_id')
    ordering = ('exam', 'display_order')


@admin.register(N2QuestionItem)
class N2QuestionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'item_order', 'correct_answer', 'updated_at')
    list_filter = ('question__exam__subcategory__section', 'question__exam__subcategory', 'question__exam')
    search_fields = ('question_text',)
    ordering = ('question', 'item_order')


@admin.register(N2MediaAsset)
class N2MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'media_type', 'source_type', 'source_basename', 'r2_key', 'updated_at')
    list_filter = ('media_type', 'source_type')
    search_fields = ('source_basename', 'source_path', 'source_url', 'r2_key', 'public_url')
    ordering = ('-created_at',)
