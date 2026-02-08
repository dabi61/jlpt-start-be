"""
Management command to import javi.json into Word table.
This command preserves the original IDs from the JSON file.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction, connection

from apps.vocabulary.models import Word


class Command(BaseCommand):
    help = 'Import javi.json into Word table, preserving original IDs'

    LEVEL_MAP = {1: 'N1', 2: 'N2', 3: 'N3', 4: 'N4', 5: 'N5'}

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default='data/javi.json',
            help='Path to javi.json file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without saving'
        )
        parser.add_argument(
            '--ids',
            type=str,
            help='Comma-separated list of IDs to import (e.g., "9870,9871,9872")'
        )
        parser.add_argument(
            '--from-units',
            action='store_true',
            help='Import only IDs referenced in units_detail.json'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        dry_run = options.get('dry_run', False)
        ids_str = options.get('ids')
        from_units = options.get('from_units', False)

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return

        # Determine which IDs to import
        target_ids = None
        if ids_str:
            target_ids = set(int(x.strip()) for x in ids_str.split(','))
            self.stdout.write(f'Importing specific IDs: {len(target_ids)} items')
        elif from_units:
            target_ids = self._get_ids_from_units()
            self.stdout.write(f'Importing IDs from units_detail.json: {len(target_ids)} items')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))

        # Load JSON
        self.stdout.write(f'Loading {json_file}...')
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f'Found {len(data)} total records')

        # Filter by target IDs if specified
        if target_ids:
            data = [r for r in data if r.get('id') in target_ids]
            self.stdout.write(f'Filtered to {len(data)} records matching target IDs')

        if dry_run:
            self._dry_run(data)
        else:
            self._import_data(data)

        self.stdout.write(self.style.SUCCESS('Done!'))

    def _get_ids_from_units(self):
        """Get all word_ids from units_detail.json."""
        units_file = 'data/units_detail.json'
        if not os.path.exists(units_file):
            self.stdout.write(self.style.ERROR(f'Units file not found: {units_file}'))
            return set()

        with open(units_file, 'r', encoding='utf-8') as f:
            units = json.load(f)

        ids = set()
        for unit in units:
            word_id = unit.get('word_id')
            if word_id:
                ids.add(word_id)
        return ids

    def _dry_run(self, data):
        """Preview import without saving."""
        levels = {}
        for record in data:
            level = record.get('level')
            if level:
                levels[level] = levels.get(level, 0) + 1

        self.stdout.write('\nRecords by level:')
        for level, count in sorted(levels.items()):
            jlpt = self.LEVEL_MAP.get(level, f'L{level}')
            self.stdout.write(f'  {jlpt}: {count}')

        # Check existing IDs
        existing_ids = set(Word.objects.values_list('id', flat=True))
        new_ids = set(r.get('id') for r in data)
        overlap = existing_ids & new_ids
        if overlap:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {len(overlap)} IDs already exist in DB'))

        self.stdout.write(f'\nWould import {len(data)} words')

    @transaction.atomic
    def _import_data(self, data):
        """Import data preserving original IDs using raw SQL."""
        imported = 0
        skipped = 0
        updated = 0

        self.stdout.write('Importing words...')

        for record in data:
            word_id = record.get('id')
            if not word_id:
                skipped += 1
                continue

            # Convert level
            level_int = record.get('level')
            level = self.LEVEL_MAP.get(level_int, '') if level_int else ''

            # Parse JSON fields
            mean = self._parse_json_field(record.get('mean'))
            synsets = self._parse_json_field(record.get('synsets'))
            opposite_word = self._parse_json_field(record.get('opposite_word'))
            related_words = self._parse_json_field(record.get('related_words'))

            # Check if word exists
            try:
                word = Word.objects.get(id=word_id)
                # Update existing
                word.j_word = record.get('word', '')
                word.phonetic = record.get('phonetic', '')
                word.short_mean = record.get('short_mean', '')
                word.mean = mean
                word.opposite_word = opposite_word
                word.synsets = synsets
                word.related_words = related_words
                word.han = record.get('han', '')
                word.grid = record.get('grid')
                word.level = level
                word.save()
                updated += 1
            except Word.DoesNotExist:
                # Insert with specific ID using raw SQL
                self._insert_word_with_id(
                    word_id=word_id,
                    j_word=record.get('word', ''),
                    phonetic=record.get('phonetic', ''),
                    short_mean=record.get('short_mean', ''),
                    mean=mean,
                    opposite_word=opposite_word,
                    synsets=synsets,
                    related_words=related_words,
                    han=record.get('han', ''),
                    grid=record.get('grid'),
                    level=level,
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(f'  Imported: {imported}'))
        self.stdout.write(f'  Updated: {updated}')
        self.stdout.write(f'  Skipped: {skipped}')

    def _parse_json_field(self, value):
        """Parse a field that might be a JSON string or already parsed."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def _insert_word_with_id(self, word_id, j_word, phonetic, short_mean, mean,
                              opposite_word, synsets, related_words, han, grid, level):
        """Insert a word with a specific ID using raw SQL."""
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vocabulary_word
                (id, j_word, phonetic, short_mean, mean, opposite_word, synsets,
                 related_words, han, grid, level, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, [
                word_id,
                j_word,
                phonetic,
                short_mean,
                json.dumps(mean) if mean else None,
                json.dumps(opposite_word) if opposite_word else None,
                json.dumps(synsets) if synsets else None,
                json.dumps(related_words) if related_words else None,
                han,
                grid,
                level,
            ])
