"""
Serializers for Grammar app.
"""
from rest_framework import serializers

from .models import Grammar


class GrammarSerializer(serializers.ModelSerializer):
    """Full serializer for Grammar model."""

    level_display = serializers.CharField(read_only=True)
    example_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Grammar
        fields = [
            'id',
            'title',
            'mean',
            'level',
            'level_display',
            'note',
            'structure',
            'about',
            'fun_fact',
            'caution',
            'examples',
            'synonyms',
            'example_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GrammarListSerializer(serializers.ModelSerializer):
    """Compact serializer for grammar list views."""

    level_display = serializers.CharField(read_only=True)

    class Meta:
        model = Grammar
        fields = [
            'id',
            'title',
            'mean',
            'level',
            'level_display',
            'structure',
        ]


class GrammarCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating grammar points."""

    class Meta:
        model = Grammar
        fields = [
            'title',
            'mean',
            'level',
            'note',
            'structure',
            'about',
            'fun_fact',
            'caution',
            'examples',
            'synonyms',
        ]
