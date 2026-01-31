"""
Management command to import learning data from JSON files.
Imports lessons, units, and unit details.
Maps unit IDs based on sequences field.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.learning.models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
)


class Command(BaseCommand):
    help = 'Import learning data from JSON files (lessons, units, units_detail)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )

    def handle(self, *args, **options):
        data_dir = Path('data')

        if options['clear']:
            self.stdout.write('Clearing existing data...')
            UnitWordDetail.objects.all().delete()
            UnitGrammarDetail.objects.all().delete()
            Unit.objects.all().delete()
            Lesson.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all learning data'))

        # Import lessons
        lessons_file = data_dir / 'lessons.json'
        if lessons_file.exists():
            self.import_lessons(lessons_file)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {lessons_file}'))

        # Import units and build mapping
        units_file = data_dir / 'units.json'
        old_to_new_unit_id = {}
        if units_file.exists():
            old_to_new_unit_id = self.import_units(units_file)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {units_file}'))

        # Import units_detail with mapping
        units_detail_file = data_dir / 'units_detail.json'
        if units_detail_file.exists():
            self.import_units_detail(units_detail_file, old_to_new_unit_id)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {units_detail_file}'))

        self.stdout.write(self.style.SUCCESS('Import completed!'))

    def import_lessons(self, file_path):
        self.stdout.write(f'Importing lessons from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for item in data:
            lesson, created = Lesson.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'lession_name': item.get('lesson_name', ''),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Lessons: {created_count} created, {updated_count} updated'
            )
        )

    def import_units(self, file_path):
        """
        Import units and map ID based on sequences field.
        Returns a mapping dict: old_id -> new_id (sequences)
        """
        self.stdout.write(f'Importing units from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0
        old_to_new = {}  # old_id -> sequences (new_id)

        for item in data:
            old_id = item.get('id')
            sequences = item.get('sequences')
            # New ID is based on sequences (convert to int)
            new_id = int(sequences) if sequences else old_id

            # Build mapping
            old_to_new[old_id] = new_id

            unit, created = Unit.objects.update_or_create(
                id=new_id,  # Use sequences as new ID
                defaults={
                    'unit_name': item.get('unit_name', ''),
                    'lession_id': str(item.get('lesson_id', '')),
                    'total': str(item.get('total', '')),
                    'unit_type': item.get('unit_type', ''),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Units: {created_count} created, {updated_count} updated'
            )
        )
        self.stdout.write(f'Unit ID mapping created: {len(old_to_new)} entries')

        return old_to_new

    def import_units_detail(self, file_path, old_to_new_unit_id):
        """
        Import units_detail with unit_id mapping.
        Maps old unit_id to new unit_id based on sequences.
        """
        self.stdout.write(f'Importing units_detail from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        word_created = 0
        grammar_created = 0

        for item in data:
            old_unit_id = item.get('unit_id')
            # Map to new unit_id based on sequences
            new_unit_id = old_to_new_unit_id.get(old_unit_id, old_unit_id)

            word_id = item.get('word_id')
            grammar_id = item.get('grammar_id')

            # Create UnitWordDetail if word_id exists
            if word_id is not None:
                UnitWordDetail.objects.update_or_create(
                    id=item.get('id'),
                    defaults={
                        'unit_id': str(new_unit_id) if new_unit_id else '',
                        'word_id': str(word_id),
                    }
                )
                word_created += 1

            # Create UnitGrammarDetail if grammar_id exists
            if grammar_id is not None:
                UnitGrammarDetail.objects.update_or_create(
                    id=item.get('id'),
                    defaults={
                        'unit_id': str(new_unit_id) if new_unit_id else '',
                        'grammar_id': str(grammar_id),
                    }
                )
                grammar_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Unit details: {word_created} word links, {grammar_created} grammar links'
            )
        )
