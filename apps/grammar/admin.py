"""
Admin configuration for Grammar app.
"""
from django.contrib import admin

from .models import Grammar


@admin.register(Grammar)
class GrammarAdmin(admin.ModelAdmin):
    """Admin configuration for Grammar model."""

    list_display = ['title', 'level_display', 'mean', 'example_count', 'updated_at']
    list_filter = ['level']
    search_fields = ['title', 'mean', 'structure', 'about']
    ordering = ['level', 'title']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'mean', 'level', 'structure')
        }),
        ('Details', {
            'fields': ('about', 'note'),
            'classes': ('collapse',)
        }),
        ('JSON Data', {
            'fields': ('examples', 'synonyms', 'fun_fact', 'caution'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def level_display(self, obj):
        return obj.level_display
    level_display.short_description = 'Level'
