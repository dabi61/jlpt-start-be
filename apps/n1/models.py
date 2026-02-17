"""
Models for JLPT N1 practice dataset (reading/listening/grammar/vocabulary).
"""
from django.db import models


class N1Section(models.Model):
    """Top-level section: Doc, Nghe, NguPhap, TuVung."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 section'
        verbose_name_plural = 'N1 sections'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class N1Subcategory(models.Model):
    """Subcategory under a section (e.g., DoanVanNgan, NgheHieuChuDe)."""

    section = models.ForeignKey(N1Section, on_delete=models.CASCADE, related_name='subcategories')
    code = models.SlugField(max_length=80)
    source_key = models.CharField(max_length=120, db_index=True)
    name = models.CharField(max_length=150)
    sort_order = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 subcategory'
        verbose_name_plural = 'N1 subcategories'
        ordering = ['section__sort_order', 'sort_order', 'name']
        unique_together = [('section', 'code'), ('section', 'source_key')]
        indexes = [
            models.Index(fields=['section', 'source_key']),
        ]

    def __str__(self):
        return f"{self.section.name} / {self.name}"


class N1Exam(models.Model):
    """One source JSON dataset under a subcategory."""

    subcategory = models.ForeignKey(N1Subcategory, on_delete=models.CASCADE, related_name='exams')
    slug = models.SlugField(max_length=120)
    name = models.CharField(max_length=200)
    source_file = models.CharField(max_length=255, unique=True)
    source_kind = models.CharField(max_length=120, blank=True, default='')

    jlpt_level = models.PositiveSmallIntegerField(default=1)
    time_limit_seconds = models.PositiveIntegerField(default=0)
    question_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 exam'
        verbose_name_plural = 'N1 exams'
        ordering = ['subcategory__sort_order', 'name']
        unique_together = [('subcategory', 'slug')]
        indexes = [
            models.Index(fields=['subcategory', 'slug']),
            models.Index(fields=['source_kind']),
        ]

    def __str__(self):
        return self.name


class N1Question(models.Model):
    """Question block from source JSON (contains one or more question items)."""

    exam = models.ForeignKey(N1Exam, on_delete=models.CASCADE, related_name='questions')
    source_id = models.BigIntegerField(db_index=True)
    display_order = models.PositiveIntegerField(default=0)

    kind = models.CharField(max_length=120, blank=True, default='')
    title = models.TextField(blank=True, default='')
    jlpt_level = models.PositiveSmallIntegerField(default=1)

    score = models.FloatField(default=0)
    scores = models.JSONField(default=list, blank=True)
    correct_answers = models.JSONField(default=list, blank=True)
    time_tracking = models.IntegerField(default=0)

    source_import = models.JSONField(default=dict, blank=True)
    raw_general = models.JSONField(default=dict, blank=True)

    general_audio_url = models.TextField(blank=True, default='')
    general_image_url = models.TextField(blank=True, default='')
    general_txt_read = models.TextField(blank=True, default='')
    general_text_read_en = models.TextField(blank=True, default='')
    general_text_read_vn = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 question'
        verbose_name_plural = 'N1 questions'
        ordering = ['exam', 'display_order', 'id']
        unique_together = [('exam', 'source_id'), ('exam', 'display_order')]
        indexes = [
            models.Index(fields=['exam', 'kind']),
            models.Index(fields=['exam', 'display_order']),
        ]

    def __str__(self):
        return f"{self.exam.name} #{self.source_id}"


class N1QuestionItem(models.Model):
    """Atomic question item inside `content` array."""

    question = models.ForeignKey(N1Question, on_delete=models.CASCADE, related_name='items')
    item_order = models.PositiveIntegerField(default=0)

    question_text = models.TextField(blank=True, default='')
    image_url = models.TextField(blank=True, default='')

    answers = models.JSONField(default=list, blank=True)
    choose_answer = models.IntegerField(null=True, blank=True)
    correct_answer = models.IntegerField(null=True, blank=True)

    explain_en = models.TextField(blank=True, default='')
    explain_vn = models.TextField(blank=True, default='')
    raw_explain = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 question item'
        verbose_name_plural = 'N1 question items'
        ordering = ['question', 'item_order', 'id']
        unique_together = [('question', 'item_order')]
        indexes = [
            models.Index(fields=['question', 'item_order']),
        ]

    def __str__(self):
        return f"{self.question_id}:{self.item_order}"


class N1MediaAsset(models.Model):
    """Uploaded media registry for source local/remote resources."""

    class SourceType(models.TextChoices):
        LOCAL = 'LOCAL', 'Local file'
        REMOTE = 'REMOTE', 'Remote URL'

    class MediaType(models.TextChoices):
        IMAGE = 'IMAGE', 'Image'
        AUDIO = 'AUDIO', 'Audio'
        OTHER = 'OTHER', 'Other'

    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    media_type = models.CharField(max_length=10, choices=MediaType.choices)

    source_url = models.TextField(blank=True, default='')
    source_path = models.CharField(max_length=500, blank=True, default='')
    source_basename = models.CharField(max_length=255, blank=True, default='', db_index=True)

    r2_key = models.CharField(max_length=500, unique=True)
    public_url = models.TextField()
    content_type = models.CharField(max_length=120, blank=True, default='')
    content_length = models.BigIntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'N1 media asset'
        verbose_name_plural = 'N1 media assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_type', 'media_type']),
            models.Index(fields=['source_basename']),
        ]

    def __str__(self):
        return self.r2_key
