"""
Word Model for Japanese Vocabulary.
"""
from django.db import models


class Word(models.Model):
    """
    Model for Japanese vocabulary words.
    Stores word data including meanings, synonyms, and related words as JSON.
    """

    class JLPTLevel(models.TextChoices):
        N6 = 'N6', 'Beginner'
        N5 = 'N5', 'N5 - Basic'
        N4 = 'N4', 'N4 - Elementary'
        N3 = 'N3', 'N3 - Intermediate'
        N2 = 'N2', 'N2 - Pre-Advanced'
        N1 = 'N1', 'N1 - Advanced'

    # Primary fields (Text)
    j_word = models.CharField(
        'Japanese word',
        max_length=100,
        db_index=True
    )
    phonetic = models.CharField(
        'phonetic reading',
        max_length=200,
        blank=True,
        null=True,
        help_text='Hiragana/Katakana reading'
    )
    short_mean = models.TextField(
        'short meaning',
        blank=True,
        null=True,
        help_text='Brief meaning summary'
    )
    han = models.CharField(
        'han/kanji',
        max_length=100,
        blank=True,
        null=True,
        help_text='Kanji characters'
    )
    grid = models.CharField(
        'stroke count',
        max_length=10,
        blank=True,
        null=True,
        help_text='Number of strokes'
    )
    level = models.CharField(
        'JLPT level',
        max_length=5,
        choices=JLPTLevel.choices,
        default=JLPTLevel.N5,
        blank=True,
        null=True,
        db_index=True
    )

    # JSON fields
    mean = models.JSONField(
        'meanings',
        default=list,
        blank=True,
        null=True,
        help_text='Array of meanings with examples: [{"mean": "...", "kind": "...", "examples": [...]}]'
    )
    opposite_word = models.JSONField(
        'opposite words',
        default=list,
        blank=True,
        null=True,
        help_text='Array of opposite words: ["word1", "word2"]'
    )
    synsets = models.JSONField(
        'synonym sets',
        default=list,
        blank=True,
        null=True,
        help_text='Array of synonym sets with definitions'
    )
    related_words = models.JSONField(
        'related words',
        default=list,
        blank=True,
        null=True,
        help_text='Array of related words'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'word'
        verbose_name_plural = 'words'
        ordering = ['level', 'j_word']
        indexes = [
            models.Index(fields=['j_word', 'level']),
        ]

    def __str__(self):
        return f"{self.j_word} ({self.level})"

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def get_all_meanings(self) -> list[str]:
        """Return flat list of all meaning strings."""
        if not self.mean or not isinstance(self.mean, list):
            return []
        meanings = []
        for item in self.mean:
            if isinstance(item, dict):
                val = item.get('mean')
                if val:
                    meanings.append(val)
            elif isinstance(item, str):
                meanings.append(item)
        return meanings

    def get_examples(self) -> list[str]:
        """Return flat list of all example IDs from meanings."""
        if not self.mean or not isinstance(self.mean, list):
            return []
        examples = []
        for item in self.mean:
            if isinstance(item, dict):
                examples.extend(item.get('examples', []))
        return examples

    def get_example_objects(self):
        """Return Example QuerySet from example IDs in meanings."""
        from apps.examples.models import Example
        example_ids = self.get_examples()
        if not example_ids:
            return Example.objects.none()
        # Convert string IDs to integers
        int_ids = []
        for eid in example_ids:
            if isinstance(eid, str) and eid.isdigit():
                int_ids.append(int(eid))
            elif isinstance(eid, int):
                int_ids.append(eid)
        return Example.objects.filter(id__in=int_ids)

    def get_synonyms(self) -> list[str]:
        """Return flat list of all synonym words from synsets."""
        if not self.synsets or not isinstance(self.synsets, list):
            return []
        synonyms = set()
        for synset in self.synsets:
            if isinstance(synset, dict):
                for entry in synset.get('entry', []):
                    if isinstance(entry, dict):
                        synonyms.update(entry.get('synonym', []))
        return list(synonyms)

    def get_opposites(self) -> list[str]:
        """Return list of opposite words."""
        return self.opposite_word if self.opposite_word else []

    def get_related(self) -> list[str]:
        """Return list of related words."""
        return self.related_words if self.related_words else []

    @property
    def is_advanced(self) -> bool:
        """Check if word is advanced level (N1 or N2)."""
        return self.level in [self.JLPTLevel.N1, self.JLPTLevel.N2]

    @property
    def is_beginner(self) -> bool:
        """Check if word is beginner level (N5 or N6)."""
        return self.level in [self.JLPTLevel.N5, self.JLPTLevel.N6]

    @property
    def meaning_count(self) -> int:
        """Return number of meanings."""
        return len(self.mean) if self.mean else 0

    @property
    def has_examples(self) -> bool:
        """Check if word has any examples."""
        return bool(self.get_examples())
