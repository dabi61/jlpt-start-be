"""
Kanji Model for storing Kanji characters and their related data.
"""
from django.db import models


class Kanji(models.Model):
    """
    Model for Kanji characters.
    Stores readings, meanings, components, and examples.
    """

    kanji = models.CharField(
        'kanji',
        max_length=10,
        blank=True,
        null=True,
        help_text='The Kanji character'
    )
    mean = models.TextField(
        'meaning',
        blank=True,
        null=True,
        help_text='Meanings in Vietnamese'
    )
    level = models.IntegerField(
        'JLPT level',
        blank=True,
        null=True,
        help_text='JLPT level as integer (5=N5, 4=N4, 3=N3, 2=N2, 1=N1)'
    )
    on = models.TextField(
        'onyomi',
        blank=True,
        null=True,
        help_text='Onyomi readings'
    )
    kun = models.TextField(
        'kunyomi',
        blank=True,
        null=True,
        help_text='Kunyomi readings'
    )
    img = models.TextField(
        'image',
        blank=True,
        null=True,
        help_text='Image URL or path'
    )
    detail = models.TextField(
        'detail',
        blank=True,
        null=True,
        help_text='Detailed description'
    )
    freq = models.CharField(
        'frequency',
        max_length=100,
        blank=True,
        null=True,
        help_text='Frequency of appearance'
    )
    comp = models.TextField(
        'components',
        blank=True,
        null=True,
        help_text='Components (string)'
    )
    stroke_count = models.IntegerField(
        'stroke count',
        blank=True,
        null=True,
        help_text='Number of strokes'
    )
    compDetail = models.JSONField(
        'component details',
        blank=True,
        null=True,
        default=list,
        help_text='List of component objects [{h, w}]'
    )
    examples = models.JSONField(
        'examples',
        blank=True,
        null=True,
        default=list,
        help_text='List of example objects [{h, m, p, w}]'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'kanji'
        verbose_name_plural = 'kanjis'
        ordering = ['level', 'kanji']
        indexes = [
            models.Index(fields=['kanji', 'level']),
        ]

    def __str__(self):
        level_str = f"N{self.level}" if self.level else "?"
        return f"{self.kanji} ({level_str})"

    @property
    def level_display(self) -> str:
        """Return level as N-format string."""
        return f"N{self.level}" if self.level else None

    @property
    def example_count(self) -> int:
        """Return number of examples."""
        if not self.examples or not isinstance(self.examples, list):
            return 0
        return len(self.examples)
