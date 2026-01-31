"""
Serializers for Vocabulary app.
"""
from rest_framework import serializers

from .models import Word
from apps.examples.serializers import ExampleSerializer


class WordSerializer(serializers.ModelSerializer):
    """Full serializer for Word model."""

    meaning_count = serializers.IntegerField(read_only=True)
    is_advanced = serializers.BooleanField(read_only=True)
    all_meanings = serializers.SerializerMethodField()
    all_synonyms = serializers.SerializerMethodField()
    examples = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            'id',
            'j_word',
            'phonetic',
            'short_mean',
            'han',
            'grid',
            'level',
            'mean',
            'opposite_word',
            'synsets',
            'related_words',
            'meaning_count',
            'is_advanced',
            'all_meanings',
            'all_synonyms',
            'examples',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_all_meanings(self, obj):
        return obj.get_all_meanings()

    def get_all_synonyms(self, obj):
        return obj.get_synonyms()

    def get_examples(self, obj):
        """Return full Example objects for this word."""
        return ExampleSerializer(obj.get_example_objects(), many=True).data


class WordListSerializer(serializers.ModelSerializer):
    """Compact serializer for word list views."""

    class Meta:
        model = Word
        fields = [
            'id',
            'j_word',
            'phonetic',
            'short_mean',
            'level',
        ]


class WordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating words."""

    class Meta:
        model = Word
        fields = [
            'j_word',
            'phonetic',
            'short_mean',
            'han',
            'grid',
            'level',
            'mean',
            'opposite_word',
            'synsets',
            'related_words',
        ]
