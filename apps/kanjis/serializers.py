"""
Serializers for Kanji app.
"""
from rest_framework import serializers

from .models import Kanji


class KanjiSerializer(serializers.ModelSerializer):
    """Full serializer for Kanji model."""

    level_display = serializers.CharField(read_only=True)
    example_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Kanji
        fields = [
            'id',
            'kanji',
            'mean',
            'level',
            'level_display',
            'on',
            'kun',
            'img',
            'detail',
            'freq',
            'comp',
            'stroke_count',
            'compDetail',
            'examples',
            'example_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class KanjiListSerializer(serializers.ModelSerializer):
    """Compact serializer for kanji list views."""

    level_display = serializers.CharField(read_only=True)

    class Meta:
        model = Kanji
        fields = [
            'id',
            'kanji',
            'mean',
            'level',
            'level_display',
            'stroke_count',
        ]
