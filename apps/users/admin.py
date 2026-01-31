"""
Admin configuration for User model.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = ('email', 'display_name', 'role', 'status', 'level', 'streak', 'date_joined')
    list_filter = ('role', 'status', 'level', 'login_method')
    search_fields = ('email', 'display_name', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('display_name', 'first_name', 'last_name', 'avatar')}),
        ('Auth & Role', {'fields': ('role', 'status', 'login_method')}),
        ('Learning Progress', {'fields': ('level', 'streak', 'last_study_date')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'display_name', 'role', 'level'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
