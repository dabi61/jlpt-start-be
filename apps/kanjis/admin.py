"""
Admin configuration for Kanji app.
"""
from django.contrib import admin

from .models import Kanji


@admin.register(Kanji)
class KanjiAdmin(admin.ModelAdmin):
    """Admin configuration for Kanji model."""

    list_display = ['kanji', 'level_display', 'mean', 'stroke_count', 'example_count', 'updated_at']
    list_filter = ['level']
    search_fields = ['kanji', 'mean', 'on', 'kun']
    ordering = ['level', 'kanji']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('kanji', 'mean', 'level', 'stroke_count', 'freq')
        }),
        ('Readings', {
            'fields': ('on', 'kun')
        }),
        ('Details', {
            'fields': ('detail', 'img', 'comp'),
            'classes': ('collapse',)
        }),
        ('JSON Data', {
            'fields': ('compDetail', 'examples'),
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
