"""
Admin configuration for Examples app.
"""
from django.contrib import admin

from .models import Example


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    """Admin configuration for Example model."""

    list_display = ['content_summary', 'mean_summary', 'created_at']
    search_fields = ['content', 'mean', 'trans']
    readonly_fields = ['created_at', 'updated_at']

    def content_summary(self, obj):
        if obj.content:
            return obj.content[:100]
        return "-"
    content_summary.short_description = 'Content'

    def mean_summary(self, obj):
        if obj.mean:
            return obj.mean[:100]
        return "-"
    mean_summary.short_description = 'Meaning'
