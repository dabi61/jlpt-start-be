from django.contrib import admin

from .models import PracticeAttempt, PracticeAnswer


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'level',
        'exam_id',
        'exam_name',
        'status',
        'answered_items',
        'correct_items',
        'score',
        'started_at',
        'submitted_at',
    )
    list_filter = ('level', 'status')
    search_fields = ('exam_name', 'section_code', 'subcategory_code', 'user__email')
    ordering = ('-started_at', '-id')


@admin.register(PracticeAnswer)
class PracticeAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'attempt',
        'question_item_id',
        'selected_answer',
        'correct_answer',
        'is_correct',
        'updated_at',
    )
    list_filter = ('is_correct',)
    search_fields = ('attempt__user__email',)
    ordering = ('-updated_at', '-id')

