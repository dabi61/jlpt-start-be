"""Serializers for N2 practice data APIs."""
from rest_framework import serializers

from .models import (
    N2Section,
    N2Subcategory,
    N2Exam,
    N2Question,
    N2QuestionItem,
    N2MediaAsset,
)


class N2SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = N2Section
        fields = [
            'id',
            'code',
            'name',
            'description',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class N2SubcategorySerializer(serializers.ModelSerializer):
    section_code = serializers.CharField(source='section.code', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = N2Subcategory
        fields = [
            'id',
            'section',
            'section_code',
            'section_name',
            'code',
            'source_key',
            'name',
            'sort_order',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'section_code', 'section_name']


class N2ExamSerializer(serializers.ModelSerializer):
    section_id = serializers.IntegerField(source='subcategory.section_id', read_only=True)
    section_code = serializers.CharField(source='subcategory.section.code', read_only=True)
    section_name = serializers.CharField(source='subcategory.section.name', read_only=True)
    subcategory_code = serializers.CharField(source='subcategory.code', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = N2Exam
        fields = [
            'id',
            'subcategory',
            'subcategory_code',
            'subcategory_name',
            'section_id',
            'section_code',
            'section_name',
            'slug',
            'name',
            'source_file',
            'source_kind',
            'jlpt_level',
            'time_limit_seconds',
            'question_count',
            'is_active',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'section_id',
            'section_code',
            'section_name',
            'subcategory_code',
            'subcategory_name',
        ]


class N2QuestionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = N2QuestionItem
        fields = [
            'id',
            'question',
            'item_order',
            'question_text',
            'image_url',
            'answers',
            'choose_answer',
            'correct_answer',
            'explain_en',
            'explain_vn',
            'raw_explain',
            'raw_data',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class N2QuestionListSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    section_code = serializers.CharField(source='exam.subcategory.section.code', read_only=True)
    subcategory_code = serializers.CharField(source='exam.subcategory.code', read_only=True)

    class Meta:
        model = N2Question
        fields = [
            'id',
            'exam',
            'exam_name',
            'section_code',
            'subcategory_code',
            'source_id',
            'display_order',
            'kind',
            'title',
            'jlpt_level',
            'score',
            'scores',
            'correct_answers',
            'time_tracking',
            'general_audio_url',
            'general_image_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'exam_name', 'section_code', 'subcategory_code']


class N2QuestionSerializer(serializers.ModelSerializer):
    items = N2QuestionItemSerializer(many=True, read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    section_code = serializers.CharField(source='exam.subcategory.section.code', read_only=True)
    subcategory_code = serializers.CharField(source='exam.subcategory.code', read_only=True)

    class Meta:
        model = N2Question
        fields = [
            'id',
            'exam',
            'exam_name',
            'section_code',
            'subcategory_code',
            'source_id',
            'display_order',
            'kind',
            'title',
            'jlpt_level',
            'score',
            'scores',
            'correct_answers',
            'time_tracking',
            'source_import',
            'raw_general',
            'general_audio_url',
            'general_image_url',
            'general_txt_read',
            'general_text_read_en',
            'general_text_read_vn',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'exam_name',
            'section_code',
            'subcategory_code',
            'items',
        ]


class N2MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = N2MediaAsset
        fields = [
            'id',
            'source_type',
            'media_type',
            'source_url',
            'source_path',
            'source_basename',
            'r2_key',
            'public_url',
            'content_type',
            'content_length',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
