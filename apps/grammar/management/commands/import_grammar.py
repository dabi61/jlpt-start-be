"""
Management command to import grammar from JSON file.

Usage:
    python manage.py import_grammar path/to/grammar.json
    python manage.py import_grammar path/to/grammar.json --update
    python manage.py import_grammar path/to/grammar.json --clean-html
"""
import json
import re
from django.core.management.base import BaseCommand
from apps.grammar.models import Grammar


def strip_html(text):
    """Remove HTML tags from text using regex (no external dependency)."""
    if not text:
        return text
    if not isinstance(text, str):
        return text
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def clean_json_html(data):
    """Recursively clean HTML from JSON data."""
    if isinstance(data, str):
        return strip_html(data)
    elif isinstance(data, list):
        return [clean_json_html(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_json_html(value) for key, value in data.items()}
    return data


def parse_level(raw_level):
    """
    Parse level to integer.
    - "N5" -> 5
    - 5 -> 5
    - "5" -> 5
    """
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
    help = 'Import grammar points from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing grammar points if found'
        )
        parser.add_argument(
            '--clean-html',
            action='store_true',
            default=True,
            help='Clean HTML tags from text fields (default: True)'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        update = options['update']
        clean_html = options['clean_html']

        self.stdout.write(f"Loading grammar from {json_file}...")

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
        self.stdout.write(f"Found {total} grammar points to import...")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, item in enumerate(data, 1):
            try:
                # Extract and clean fields
                # NOTE: In the JSON, the grammar title is under the 'key' field
                title = item.get('key', '')
                if clean_html:
                    title = strip_html(title)

                mean = item.get('mean', '')
                if clean_html:
                    mean = strip_html(mean)

                level = parse_level(item.get('level'))

                note = item.get('note', '')
                if clean_html:
                    note = strip_html(note)

                structure = item.get('structure', '')
                if clean_html:
                    structure = strip_html(structure)

                about = item.get('about', '')
                if clean_html:
                    about = strip_html(about)

                # JSON fields - clean HTML inside
                fun_fact = item.get('fun_fact', [])
                caution = item.get('caution', [])
                examples = item.get('examples', [])
                synonyms = item.get('synonyms', [])

                if clean_html:
                    fun_fact = clean_json_html(fun_fact)
                    caution = clean_json_html(caution)
                    examples = clean_json_html(examples)
                    synonyms = clean_json_html(synonyms)

                grammar_data = {
                    'title': title or None,
                    'mean': mean or None,
                    'level': level,
                    'note': note or None,
                    'structure': structure or None,
                    'about': about or None,
                    'fun_fact': fun_fact if fun_fact else None,
                    'caution': caution if caution else None,
                    'examples': examples if examples else None,
                    'synonyms': synonyms if synonyms else None,
                }

                # Check for existing (by title + level)
                existing = None
                if title:
                    existing = Grammar.objects.filter(title=title, level=level).first()

                if existing:
                    if update:
                        # Smart merge: only update if new value is present
                        did_update = False
                        for key, value in grammar_data.items():
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
                    Grammar.objects.create(**grammar_data)
                    created_count += 1

                if i % 100 == 0:
                    self.stdout.write(f"Processed {i}/{total} grammar points...")

            except Exception as e:
                self.stderr.write(f"Error importing grammar {i}: {str(e)}")
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete!\n"
            f"  Created: {created_count}\n"
            f"  Updated: {updated_count}\n"
            f"  Skipped: {skipped_count}\n"
            f"  Errors:  {error_count}"
        ))
