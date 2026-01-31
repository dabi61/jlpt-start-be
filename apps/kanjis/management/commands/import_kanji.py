"""
Management command to import Kanji from JSON file.
"""
import json
from django.core.management.base import BaseCommand
from apps.kanjis.models import Kanji


def parse_level(raw_level):
    """Parse level to integer."""
    if raw_level is None:
        return None
    if isinstance(raw_level, int):
        return raw_level
    raw_str = str(raw_level).strip().upper()
    if raw_str.startswith('N') and len(raw_str) == 2:
        try:
            return int(raw_str[1])
        except ValueError:
            return None
    try:
        return int(raw_str)
    except ValueError:
        return None


class Command(BaseCommand):
    help = 'Import Kanji points from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing kanji points if found'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        update = options['update']

        self.stdout.write(f"Loading Kanji from {json_file}...")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {json_file}"))
            return
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"JSON decode error: {e}"))
            return

        if not isinstance(data, list):
            data = [data]

        total = len(data)
        self.stdout.write(f"Found {total} Kanji to import...")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, item in enumerate(data, 1):
            try:
                kanji_char = item.get('kanji', '').strip()
                if not kanji_char:
                    skipped_count += 1
                    continue

                level = parse_level(item.get('level'))

                kanji_data = {
                    'kanji': kanji_char,
                    'mean': item.get('mean'),
                    'level': level,
                    'on': item.get('on'),
                    'kun': item.get('kun'),
                    'img': item.get('img'),
                    'detail': item.get('detail'),
                    'freq': item.get('freq'),
                    'comp': item.get('comp'),
                    'stroke_count': item.get('stroke_count'),
                    'compDetail': item.get('compDetail', []),
                    'examples': item.get('examples', []),
                }

                # Check for existing
                existing = Kanji.objects.filter(kanji=kanji_char).first()

                if existing:
                    if update:
                        did_update = False
                        for key, value in kanji_data.items():
                            if value not in [None, '', [], {}]:
                                current_value = getattr(existing, key)
                                if current_value != value:
                                    setattr(existing, key, value)
                                    did_update = True

                        if did_update:
                            existing.save()
                            updated_count += 1
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                else:
                    Kanji.objects.create(**kanji_data)
                    created_count += 1

                if i % 100 == 0:
                    self.stdout.write(f"Processed {i}/{total} Kanji...")

            except Exception as e:
                self.stderr.write(f"Error importing Kanji {i}: {str(e)}")
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete!\n"
            f"  Created: {created_count}\n"
            f"  Updated: {updated_count}\n"
            f"  Skipped: {skipped_count}\n"
            f"  Errors:  {error_count}"
        ))
