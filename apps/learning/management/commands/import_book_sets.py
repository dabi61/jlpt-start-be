"""
Management command to import book_set JSON data into the active learning schema.

Source files:
- data/book_set.json
- data/book_set_unit.json
- data/book_set_unit_detail.json

Target models:
- Lesson
- Unit
- UnitWordDetail
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.learning.models import Lesson, Unit, UnitWordDetail


class Command(BaseCommand):
    help = 'Import book set data into Lesson/Unit/UnitWordDetail'

    LEVEL_MAP = {
        '1': 'N1',
        '2': 'N2',
        '3': 'N3',
        '4': 'N4',
        '5': 'N5',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete previously imported book-set lessons before importing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview counts only, no write',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        clear = options.get('clear', False)

        data_dir = Path('data')
        book_sets = self._load_json(data_dir / 'book_set.json')
        book_set_units = self._load_json(data_dir / 'book_set_unit.json')
        book_set_unit_details = self._load_json(data_dir / 'book_set_unit_detail.json')

        if book_sets is None or book_set_units is None or book_set_unit_details is None:
            return

        # Build quick lookup by source id.
        book_set_lookup = {self._norm_id(item.get('id')): item for item in book_sets if item.get('id') is not None}

        self.stdout.write(f'Book sets: {len(book_sets)}')
        self.stdout.write(f'Book set units: {len(book_set_units)}')
        self.stdout.write(f'Book set unit details: {len(book_set_unit_details)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no data will be written'))
            return

        if clear:
            self._clear_existing(book_sets)

        self._import(book_set_lookup, book_set_units, book_set_unit_details)
        self.stdout.write(self.style.SUCCESS('Book set import completed!'))

    def _load_json(self, file_path: Path):
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _norm_id(self, value):
        if value is None:
            return None
        return str(value)

    def _lesson_name(self, book_set):
        base_name = (book_set.get('name') or '').strip() or 'BookSet'
        level = self.LEVEL_MAP.get(self._norm_id(book_set.get('level')), '')
        if level:
            return f'{base_name} {level}', level
        return base_name, ''

    def _clear_existing(self, book_sets):
        lesson_names = []
        for item in book_sets:
            lesson_name, _ = self._lesson_name(item)
            lesson_names.append(lesson_name)

        lesson_ids = list(
            Lesson.objects.filter(lession_name__in=lesson_names).values_list('id', flat=True)
        )
        unit_ids = list(
            Unit.objects.filter(lession_id__in=[str(x) for x in lesson_ids]).values_list('id', flat=True)
        )

        details_deleted = UnitWordDetail.objects.filter(unit_id__in=[str(x) for x in unit_ids]).delete()[0]
        units_deleted = Unit.objects.filter(id__in=unit_ids).delete()[0]
        lessons_deleted = Lesson.objects.filter(id__in=lesson_ids).delete()[0]

        self.stdout.write(
            self.style.WARNING(
                f'Cleared previous import: lessons={lessons_deleted}, units={units_deleted}, unit_word_details={details_deleted}'
            )
        )

    @transaction.atomic
    def _import(self, book_set_lookup, book_set_units, book_set_unit_details):
        lesson_map = {}
        created_lessons = 0
        updated_lessons = 0

        # 1) Ensure lessons exist for each book set.
        for book_set_id, book_set in sorted(
            book_set_lookup.items(),
            key=lambda x: (0, int(x[0])) if str(x[0]).isdigit() else (1, str(x[0])),
        ):
            lesson_name, level = self._lesson_name(book_set)
            lesson, created = Lesson.objects.update_or_create(
                lession_name=lesson_name,
                defaults={'level': level}
            )
            lesson_map[book_set_id] = lesson
            if created:
                created_lessons += 1
            else:
                updated_lessons += 1

        self.stdout.write(
            self.style.SUCCESS(f'Lessons: {created_lessons} created, {updated_lessons} updated')
        )

        # 2) Import units and keep mapping old_unit_id -> new_unit_id.
        unit_id_map = {}
        created_units = 0
        updated_units = 0
        skipped_units = 0

        for row in book_set_units:
            old_unit_id = self._norm_id(row.get('id'))
            book_set_id = self._norm_id(row.get('book_set_id'))
            lesson = lesson_map.get(book_set_id)

            if old_unit_id is None or lesson is None:
                skipped_units += 1
                continue

            source_book_set = book_set_lookup.get(book_set_id, {})
            source_name = (source_book_set.get('name') or '').strip()
            level = self.LEVEL_MAP.get(self._norm_id(source_book_set.get('level')), '')
            unit_name = (row.get('name') or '').strip()
            merged_name = f'{source_name} {level} - {unit_name}'.strip(' -')

            unit, created = Unit.objects.update_or_create(
                lession_id=str(lesson.id),
                unit_name=merged_name,
                defaults={
                    'total': str(row.get('total_word', '')),
                    'unit_type': 'vocabulary',
                    'level': lesson.level,
                }
            )
            unit_id_map[old_unit_id] = str(unit.id)
            if created:
                created_units += 1
            else:
                updated_units += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Units: {created_units} created, {updated_units} updated, {skipped_units} skipped'
            )
        )

        # 3) Import unit-word links.
        created_links = 0
        skipped_links = 0
        for row in book_set_unit_details:
            old_unit_id = self._norm_id(row.get('unit_id'))
            word_id = self._norm_id(row.get('word_id'))
            new_unit_id = unit_id_map.get(old_unit_id)

            if new_unit_id is None or word_id is None:
                skipped_links += 1
                continue

            _, created = UnitWordDetail.objects.get_or_create(
                unit_id=new_unit_id,
                word_id=word_id,
            )
            if created:
                created_links += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'UnitWordDetail: {created_links} created, {skipped_links} skipped'
            )
        )
