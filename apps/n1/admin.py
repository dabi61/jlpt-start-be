from django.contrib import admin

from .models import (
    N1Section,
    N1Subcategory,
    N1Exam,
    N1Question,
    N1QuestionItem,
    N1MediaAsset,
)


@admin.register(N1Section)
class N1SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'sort_order', 'updated_at')
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'name')


@admin.register(N1Subcategory)
class N1SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'section', 'code', 'source_key', 'sort_order', 'updated_at')
    list_filter = ('section',)
    search_fields = ('name', 'code', 'source_key')
    ordering = ('section__sort_order', 'sort_order', 'name')


@admin.register(N1Exam)
class N1ExamAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'subcategory', 'source_kind', 'question_count', 'time_limit_seconds', 'is_active', 'updated_at'
    )
    list_filter = ('subcategory__section', 'subcategory', 'is_active')
    search_fields = ('name', 'slug', 'source_file', 'source_kind')
    ordering = ('subcategory__sort_order', 'name')


@admin.register(N1Question)
class N1QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'source_id', 'display_order', 'kind', 'jlpt_level', 'score', 'updated_at')
    list_filter = ('exam__subcategory__section', 'exam__subcategory', 'exam', 'kind', 'jlpt_level')
    search_fields = ('title', 'kind', 'source_id')
    ordering = ('exam', 'display_order')


@admin.register(N1QuestionItem)
class N1QuestionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'item_order', 'correct_answer', 'updated_at')
    list_filter = ('question__exam__subcategory__section', 'question__exam__subcategory', 'question__exam')
    search_fields = ('question_text',)
    ordering = ('question', 'item_order')


@admin.register(N1MediaAsset)
class N1MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'media_type', 'source_type', 'source_basename', 'r2_key', 'updated_at')
    list_filter = ('media_type', 'source_type')
    search_fields = ('source_basename', 'source_path', 'source_url', 'r2_key', 'public_url')
    ordering = ('-created_at',)
