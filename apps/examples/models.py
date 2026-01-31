"""
Example Model for storing example Japanese sentences.
"""
from django.db import models


class Example(models.Model):
    """
    Model for Japanese example sentences.
    Provides content, meaning, and transcription.
    """

    content = models.TextField(
        'content',
        blank=True,
        null=True,
        help_text='The Japanese sentence'
    )
    mean = models.TextField(
        'meaning',
        blank=True,
        null=True,
        help_text='Meaning in Vietnamese'
    )
    trans = models.TextField(
        'transcription',
        blank=True,
        null=True,
        help_text='Transcription/Reading'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'example'
        verbose_name_plural = 'examples'
        ordering = ['-created_at']

    def __str__(self):
        if self.content:
            return self.content[:50] + ('...' if len(self.content) > 50 else '')
        return f"Example {self.id}"
