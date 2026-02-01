"""
Serializers for Learning app.
"""
from rest_framework import serializers

from .models import (
    Lesson,
    Unit,

    UserUnitProgress,
)


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = ['id', 'lession_name', 'level', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit model."""

    class Meta:
        model = Unit
        fields = ['id', 'unit_name', 'lession_id', 'total', 'unit_type', 'level', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']





class UserUnitProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserUnitProgress model."""

    class Meta:
        model = UserUnitProgress
        fields = ['id', 'unit_id', 'lession_id', 'progress', 'completed_at', 'user_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



