"""
Serializers for Learning app.
"""
from rest_framework import serializers

from .models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UserUnitProgress,
    BookSet,
    BookSetUnit,
    BookSetUnitDetail,
)


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = ['id', 'lession_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit model."""

    class Meta:
        model = Unit
        fields = ['id', 'unit_name', 'lession_id', 'total', 'unit_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitWordDetailSerializer(serializers.ModelSerializer):
    """Serializer for UnitWordDetail model."""

    class Meta:
        model = UnitWordDetail
        fields = ['id', 'unit_id', 'word_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitGrammarDetailSerializer(serializers.ModelSerializer):
    """Serializer for UnitGrammarDetail model."""

    class Meta:
        model = UnitGrammarDetail
        fields = ['id', 'unit_id', 'grammar_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitKanjiDetailSerializer(serializers.ModelSerializer):
    """Serializer for UnitKanjiDetail model."""

    class Meta:
        model = UnitKanjiDetail
        fields = ['id', 'unit_id', 'kanji_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserUnitProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserUnitProgress model."""

    class Meta:
        model = UserUnitProgress
        fields = ['id', 'unit_id', 'lession_id', 'progress', 'completed_at', 'user_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookSetSerializer(serializers.ModelSerializer):
    """Serializer for BookSet model."""

    class Meta:
        model = BookSet
        fields = ['id', 'name', 'level', 'total_word', 'version', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookSetUnitSerializer(serializers.ModelSerializer):
    """Serializer for BookSetUnit model."""

    class Meta:
        model = BookSetUnit
        fields = ['id', 'book_set_id', 'name', 'total_word', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookSetUnitDetailSerializer(serializers.ModelSerializer):
    """Serializer for BookSetUnitDetail model."""

    class Meta:
        model = BookSetUnitDetail
        fields = ['id', 'unit_id', 'word_id', 'sub_word', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
