"""
Management command to fix mean field data type (string → JSON).
"""
import json
from django.core.management.base import BaseCommand
from apps.vocabulary.models import Word


class Command(BaseCommand):
    help = 'Fix mean field by converting JSON strings to actual JSON objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("Scanning words with string mean field...")

        words = Word.objects.exclude(mean__isnull=True)
        total = words.count()
        fixed = 0
        already_ok = 0
        errors = 0

        for i, word in enumerate(words, 1):
            try:
                if isinstance(word.mean, str):
                    # Parse JSON string to actual JSON
                    parsed = json.loads(word.mean)
                    if not dry_run:
                        word.mean = parsed
                        word.save(update_fields=['mean'])
                    fixed += 1
                    if i <= 5:
                        self.stdout.write(f"  Fixed: {word.j_word}")
                elif isinstance(word.mean, list):
                    already_ok += 1

                if i % 1000 == 0:
                    self.stdout.write(f"Processed {i}/{total}...")

            except json.JSONDecodeError as e:
                self.stderr.write(f"  JSON Error for {word.j_word}: {e}")
                errors += 1
            except Exception as e:
                self.stderr.write(f"  Error for {word.j_word}: {e}")
                errors += 1

        mode = "DRY RUN" if dry_run else "COMPLETE"
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode}!\n"
            f"  Fixed: {fixed}\n"
            f"  Already OK: {already_ok}\n"
            f"  Errors: {errors}"
        ))
