"""
Management command to create JLPT Lessons and Units.
Creates lessons for N5-N1 levels and distributes vocabulary, grammar, and kanji into units.
"""
import math
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.learning.models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
)
from apps.vocabulary.models import Word
from apps.grammar.models import Grammar
from apps.kanjis.models import Kanji


class Command(BaseCommand):
    help = 'Create JLPT lessons (N5-N1) with vocabulary, grammar, and kanji units'

    # Configuration
    WORDS_PER_UNIT = 20
    GRAMMAR_PER_UNIT = 3
    KANJI_PER_UNIT = 5

    LEVELS = ['N5', 'N4', 'N3', 'N2', 'N1']
    LEVEL_MAP = {'N5': 5, 'N4': 4, 'N3': 3, 'N2': 2, 'N1': 1}

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            choices=self.LEVELS,
            help='Only create for specific level (N5, N4, N3, N2, N1)'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['vocabulary', 'grammar', 'kanji'],
            help='Only create specific type of units'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without saving to database'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        target_level = options.get('level')
        target_type = options.get('type')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))

        levels = [target_level] if target_level else self.LEVELS

        for level in levels:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.HTTP_INFO(f'Processing {level}...'))
            self.stdout.write(f'{"="*60}')

            if dry_run:
                self._dry_run_level(level, target_type)
            else:
                self._create_level(level, target_type)

        self.stdout.write(self.style.SUCCESS('\nDone!'))

    def _dry_run_level(self, level: str, target_type: str = None):
        """Show what would be created without saving."""
        level_int = self.LEVEL_MAP[level]

        # Count existing data
        word_count = Word.objects.filter(level=level).count()
        grammar_count = Grammar.objects.filter(level=level_int).count()
        kanji_count = Kanji.objects.filter(level=level_int).count()

        self.stdout.write(f'\nData available for {level}:')
        self.stdout.write(f'  Words: {word_count}')
        self.stdout.write(f'  Grammar: {grammar_count}')
        self.stdout.write(f'  Kanji: {kanji_count}')

        units_summary = []

        if not target_type or target_type == 'vocabulary':
            word_units = math.ceil(word_count / self.WORDS_PER_UNIT)
            units_summary.append(f'  Vocabulary units: {word_units} (20 words each)')

        if not target_type or target_type == 'grammar':
            grammar_units = math.ceil(grammar_count / self.GRAMMAR_PER_UNIT)
            units_summary.append(f'  Grammar units: {grammar_units} (3 grammar each)')

        if not target_type or target_type == 'kanji':
            kanji_units = math.ceil(kanji_count / self.KANJI_PER_UNIT)
            units_summary.append(f'  Kanji units: {kanji_units} (5 kanji each)')

        self.stdout.write(f'\nUnits to be created:')
        for summary in units_summary:
            self.stdout.write(summary)

    @transaction.atomic
    def _create_level(self, level: str, target_type: str = None):
        """Create lesson and units for a specific JLPT level."""
        level_int = self.LEVEL_MAP[level]

        # Check if lesson already exists
        lesson_name = f'JLPT {level}'
        existing_lesson = Lesson.objects.filter(lession_name=lesson_name).first()

        if existing_lesson:
            self.stdout.write(self.style.WARNING(
                f'Lesson "{lesson_name}" already exists (ID: {existing_lesson.id}). Skipping...'
            ))
            return

        # Create lesson
        lesson = Lesson.objects.create(
            lession_name=lesson_name,
            level=level
        )
        self.stdout.write(self.style.SUCCESS(f'Created Lesson: {lesson_name} (ID: {lesson.id})'))

        # Create vocabulary units
        if not target_type or target_type == 'vocabulary':
            self._create_vocabulary_units(lesson, level)

        # Create grammar units
        if not target_type or target_type == 'grammar':
            self._create_grammar_units(lesson, level_int)

        # Create kanji units
        if not target_type or target_type == 'kanji':
            self._create_kanji_units(lesson, level_int)

    def _create_vocabulary_units(self, lesson: Lesson, level: str):
        """Create vocabulary units for a lesson."""
        words = list(Word.objects.filter(level=level).order_by('id').values_list('id', flat=True))
        total_words = len(words)

        if total_words == 0:
            self.stdout.write(f'  No words found for {level}')
            return

        total_units = math.ceil(total_words / self.WORDS_PER_UNIT)
        self.stdout.write(f'  Creating {total_units} vocabulary units from {total_words} words...')

        units_to_create = []
        details_to_create = []

        for i in range(total_units):
            start_idx = i * self.WORDS_PER_UNIT
            end_idx = min((i + 1) * self.WORDS_PER_UNIT, total_words)
            chunk = words[start_idx:end_idx]

            unit_name = f'{level} - Từ vựng - Bài {i + 1}'
            units_to_create.append(Unit(
                unit_name=unit_name,
                lession_id=str(lesson.id),
                total=str(len(chunk)),
                unit_type='vocabulary',
                level=lesson.level
            ))

        # Bulk create units
        created_units = Unit.objects.bulk_create(units_to_create)
        self.stdout.write(f'    Created {len(created_units)} vocabulary units')

        # Create unit details
        for i, unit in enumerate(created_units):
            start_idx = i * self.WORDS_PER_UNIT
            end_idx = min((i + 1) * self.WORDS_PER_UNIT, total_words)
            chunk = words[start_idx:end_idx]

            for word_id in chunk:
                details_to_create.append(UnitWordDetail(
                    unit_id=str(unit.id),
                    word_id=str(word_id)
                ))

        # Bulk create details
        UnitWordDetail.objects.bulk_create(details_to_create, batch_size=1000)
        self.stdout.write(f'    Created {len(details_to_create)} word details')

    def _create_grammar_units(self, lesson: Lesson, level_int: int):
        """Create grammar units for a lesson."""
        grammars = list(Grammar.objects.filter(level=level_int).order_by('id').values_list('id', flat=True))
        total_grammar = len(grammars)

        if total_grammar == 0:
            self.stdout.write(f'  No grammar found for N{level_int}')
            return

        total_units = math.ceil(total_grammar / self.GRAMMAR_PER_UNIT)
        self.stdout.write(f'  Creating {total_units} grammar units from {total_grammar} grammar points...')

        units_to_create = []
        details_to_create = []

        for i in range(total_units):
            start_idx = i * self.GRAMMAR_PER_UNIT
            end_idx = min((i + 1) * self.GRAMMAR_PER_UNIT, total_grammar)
            chunk = grammars[start_idx:end_idx]

            unit_name = f'N{level_int} - Ngữ pháp - Bài {i + 1}'
            units_to_create.append(Unit(
                unit_name=unit_name,
                lession_id=str(lesson.id),
                total=str(len(chunk)),
                unit_type='grammar',
                level=lesson.level
            ))

        # Bulk create units
        created_units = Unit.objects.bulk_create(units_to_create)
        self.stdout.write(f'    Created {len(created_units)} grammar units')

        # Create unit details
        for i, unit in enumerate(created_units):
            start_idx = i * self.GRAMMAR_PER_UNIT
            end_idx = min((i + 1) * self.GRAMMAR_PER_UNIT, total_grammar)
            chunk = grammars[start_idx:end_idx]

            for grammar_id in chunk:
                details_to_create.append(UnitGrammarDetail(
                    unit_id=str(unit.id),
                    grammar_id=str(grammar_id)
                ))

        # Bulk create details
        UnitGrammarDetail.objects.bulk_create(details_to_create, batch_size=1000)
        self.stdout.write(f'    Created {len(details_to_create)} grammar details')

    def _create_kanji_units(self, lesson: Lesson, level_int: int):
        """Create kanji units for a lesson."""
        kanjis = list(Kanji.objects.filter(level=level_int).order_by('id').values_list('id', flat=True))
        total_kanji = len(kanjis)

        if total_kanji == 0:
            self.stdout.write(f'  No kanji found for N{level_int}')
            return

        total_units = math.ceil(total_kanji / self.KANJI_PER_UNIT)
        self.stdout.write(f'  Creating {total_units} kanji units from {total_kanji} kanji...')

        units_to_create = []
        details_to_create = []

        for i in range(total_units):
            start_idx = i * self.KANJI_PER_UNIT
            end_idx = min((i + 1) * self.KANJI_PER_UNIT, total_kanji)
            chunk = kanjis[start_idx:end_idx]

            unit_name = f'N{level_int} - Hán tự - Bài {i + 1}'
            units_to_create.append(Unit(
                unit_name=unit_name,
                lession_id=str(lesson.id),
                total=str(len(chunk)),
                unit_type='kanji',
                level=lesson.level
            ))

        # Bulk create units
        created_units = Unit.objects.bulk_create(units_to_create)
        self.stdout.write(f'    Created {len(created_units)} kanji units')

        # Create unit details
        for i, unit in enumerate(created_units):
            start_idx = i * self.KANJI_PER_UNIT
            end_idx = min((i + 1) * self.KANJI_PER_UNIT, total_kanji)
            chunk = kanjis[start_idx:end_idx]

            for kanji_id in chunk:
                details_to_create.append(UnitKanjiDetail(
                    unit_id=str(unit.id),
                    kanji_id=str(kanji_id)
                ))

        # Bulk create details
        UnitKanjiDetail.objects.bulk_create(details_to_create, batch_size=1000)
        self.stdout.write(f'    Created {len(details_to_create)} kanji details')
