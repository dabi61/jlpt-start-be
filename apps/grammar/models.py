"""
Grammar Model for Japanese Grammar Points.
"""
from django.db import models


class Grammar(models.Model):
    """
    Model for Japanese grammar points.
    Stores grammar data including examples, synonyms, caution notes as JSON.
    """

    title = models.TextField(
        'title',
        blank=True,
        null=True,
        help_text='Grammar point title (e.g., あれ)'
    )
    mean = models.TextField(
        'meaning',
        blank=True,
        null=True,
        help_text='Meaning in Vietnamese'
    )
    level = models.IntegerField(
        'JLPT level',
        blank=True,
        null=True,
        help_text='JLPT level as integer (5=N5, 4=N4, 3=N3, 2=N2, 1=N1)'
    )
    note = models.TextField(
        'note',
        blank=True,
        null=True,
        help_text='Additional notes'
    )
    structure = models.TextField(
        'structure',
        blank=True,
        null=True,
        help_text='Grammar structure/pattern'
    )
    about = models.TextField(
        'about',
        blank=True,
        null=True,
        help_text='Description about the grammar point'
    )
    fun_fact = models.JSONField(
        'fun facts',
        blank=True,
        null=True,
        default=list,
        help_text='List of fun facts'
    )
    caution = models.JSONField(
        'cautions',
        blank=True,
        null=True,
        default=list,
        help_text='List of caution notes'
    )
    examples = models.JSONField(
        'examples',
        blank=True,
        null=True,
        default=list,
        help_text='List of example sentences [{example, mean}]'
    )
    synonyms = models.JSONField(
        'synonyms',
        blank=True,
        null=True,
        default=list,
        help_text='List of related grammar [{example, mean}]'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'grammar'
        verbose_name_plural = 'grammars'
        ordering = ['level', 'title']
        indexes = [
            models.Index(fields=['title', 'level']),
        ]

    def __str__(self):
        level_str = f"N{self.level}" if self.level else "?"
        return f"{self.title} ({level_str})"

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def get_examples_list(self) -> list[dict]:
        """Return list of example dictionaries."""
        if not self.examples or not isinstance(self.examples, list):
            return []
        return self.examples

    def get_synonyms_list(self) -> list[dict]:
        """Return list of synonym dictionaries."""
        if not self.synonyms or not isinstance(self.synonyms, list):
            return []
        return self.synonyms

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
