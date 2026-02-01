"""
Management command to import javi_content.json into Word table.
Creates a mapping file for Phase 2 (remap UnitWordDetail).
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.vocabulary.models import Word


class Command(BaseCommand):
    help = 'Import javi_content.json into Word table with c0id mapping'

    LEVEL_MAP = {'1': 'N1', '2': 'N2', '3': 'N3', '4': 'N4', '5': 'N5'}

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to javi_content.json file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without saving'
        )
        parser.add_argument(
            '--output-mapping',
            type=str,
            default='docs/c0id_to_word_id_mapping.json',
            help='Path to save mapping file'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        dry_run = options.get('dry_run', False)
        mapping_file = options.get('output_mapping')

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))

        # Load JSON
        self.stdout.write(f'Loading {json_file}...')
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f'Found {len(data)} records')

        if dry_run:
            self._dry_run(data)
        else:
            mapping = self._import_data(data)
            self._save_mapping(mapping, mapping_file)

        self.stdout.write(self.style.SUCCESS('Done!'))

    def _dry_run(self, data):
        """Preview import without saving."""
        levels = {}
        for record in data:
            level = record.get('c10level')
            if level:
                levels[level] = levels.get(level, 0) + 1

        self.stdout.write('\nRecords by level:')
        for level, count in sorted(levels.items()):
            jlpt = self.LEVEL_MAP.get(str(level), f'L{level}')
            self.stdout.write(f'  {jlpt}: {count}')

        self.stdout.write(f'\nWould import {len(data)} words')

    @transaction.atomic
    def _import_data(self, data):
        """Import data and return c0id → word_id mapping."""
        mapping = {}
        imported = 0
        skipped = 0

        self.stdout.write('Importing words...')

        # Batch create for performance
        words_to_create = []
        c0ids = []

        for record in data:
            c0id = record.get('c0id')
            if not c0id:
                skipped += 1
                continue

            # Convert level
            level_int = record.get('c10level')
            level = self.LEVEL_MAP.get(str(level_int), '') if level_int else ''

            # Handle JSON fields
            mean = record.get('c4mean')
            if isinstance(mean, str):
                try:
                    mean = json.loads(mean)
                except:
                    pass

            synsets = record.get('c6synsets')
            if isinstance(synsets, str):
                try:
                    synsets = json.loads(synsets)
                except:
                    pass

            related_words = record.get('c7related_words')
            if isinstance(related_words, str):
                try:
                    related_words = json.loads(related_words)
                except:
                    pass

            word = Word(
                j_word=record.get('c1word', ''),
                phonetic=record.get('c2phonetic', ''),
                short_mean=record.get('c3short_mean', ''),
                mean=mean,
                opposite_word=record.get('c5opposite_word'),
                synsets=synsets,
                related_words=related_words,
                han=record.get('c8han', ''),
                grid=record.get('c9grid'),
                level=level,
            )
            words_to_create.append(word)
            c0ids.append(c0id)

        # Bulk create
        self.stdout.write(f'  Creating {len(words_to_create)} words...')
        created_words = Word.objects.bulk_create(words_to_create, batch_size=500)

        # Build mapping
        for i, word in enumerate(created_words):
            c0id = c0ids[i]
            mapping[str(c0id)] = word.id
            imported += 1

        self.stdout.write(self.style.SUCCESS(f'  Imported: {imported}'))
        self.stdout.write(f'  Skipped: {skipped}')

        return mapping

    def _save_mapping(self, mapping, filepath):
        """Save c0id → word_id mapping to JSON file."""
        self.stdout.write(f'Saving mapping to {filepath}...')

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2)

        self.stdout.write(f'  Saved {len(mapping)} mappings')
