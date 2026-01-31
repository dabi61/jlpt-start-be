"""
Management command to import vocabulary from JSON file.

Usage:
    python manage.py import_vocabulary path/to/vocab.json
    python manage.py import_vocabulary path/to/vocab.json --level N5
    python manage.py import_vocabulary path/to/vocab.json --clear
"""
import json
from django.core.management.base import BaseCommand, CommandError
from apps.vocabulary.models import Word


class Command(BaseCommand):
    help = 'Import vocabulary words from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON file containing vocabulary data'
        )
        parser.add_argument(
            '--level',
            type=str,
            default=None,
            help='Override JLPT level for all imported words (e.g., N5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing words before import'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing words instead of skipping'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        level_override = options['level']
        clear = options['clear']
        update = options['update']

        # Read JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {json_file}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")

        # Ensure data is a list
        if isinstance(data, dict):
            # If it's a dict, try to find the list inside
            data = data.get('words', data.get('data', [data]))

        if not isinstance(data, list):
            data = [data]

        self.stdout.write(f"Found {len(data)} words to import...")

        # Clear existing words if requested
        if clear:
            deleted_count = Word.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing words"))

        # Import words
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, item in enumerate(data, 1):
            try:
                # Map fields from source JSON to model
                word_data = self._map_fields(item, level_override)

                # Check if word exists
                j_word = word_data.get('j_word', '')
                level = word_data.get('level', 'N5')

                existing = Word.objects.filter(j_word=j_word, level=level).first()

                if existing:
                    if update:
                        updated = False
                        for key, value in word_data.items():
                            # Smart merge: Only update if new value is truthy (has data)
                            # preventing overwriting good data with nulls/empty from duplicates
                            if value not in [None, '', [], {}]:
                                current_value = getattr(existing, key)
                                # Update if current is empty or different
                                if current_value != value:
                                    setattr(existing, key, value)
                                    updated = True

                        if updated:
                            existing.save()
                            updated_count += 1
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                else:
                    Word.objects.create(**word_data)
                    created_count += 1

                # Progress indicator
                if i % 100 == 0:
                    self.stdout.write(f"Processed {i}/{len(data)} words...")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error importing word {i}: {e}")
                )

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete!"
            f"\n  Created: {created_count}"
            f"\n  Updated: {updated_count}"
            f"\n  Skipped: {skipped_count}"
            f"\n  Errors:  {error_count}"
        ))

    def _map_fields(self, item: dict, level_override: str = None) -> dict:
        """
        Map source JSON fields to Word model fields.

        Expected source format:
        {
            "id": "...",
            "word": "未来",
            "phonetic": "みらい",
            "short_mean": "tương lai",
            "mean": [...],
            "opposite_word": [...],
            "synsets": [...],
            "related_words": [...],
            "han": "...",
            "grid": "12",
            "level": "N5"
        }
        """
        # Get level
        raw_level = item.get('level')
        if level_override:
            level = level_override
        elif raw_level is not None and str(raw_level).strip():
            level_str = str(raw_level).strip().upper()
            if level_str.isdigit():
                level = f'N{level_str}'
            elif level_str.startswith('N'):
                level = level_str
            else:
                level = None
        else:
            level = None

        return {
            'j_word': item.get('word', item.get('j_word', '')),
            'phonetic': item.get('phonetic', ''),
            'short_mean': item.get('short_mean', ''),
            'han': item.get('han'),
            'grid': str(item.get('grid', '')) if item.get('grid') is not None else None,
            'level': level,
            'mean': item.get('mean'),
            'opposite_word': item.get('opposite_word'),
            'synsets': item.get('synsets'),
            'related_words': item.get('related_words'),
        }
