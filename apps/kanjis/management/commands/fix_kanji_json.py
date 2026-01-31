"""
Management command to fix JSON fields stored as strings in Kanji model.
"""
import json
from django.core.management.base import BaseCommand
from apps.kanjis.models import Kanji


class Command(BaseCommand):
    help = 'Fix JSON fields (compDetail, examples) stored as strings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("Scanning Kanji records with string JSON fields...")

        kanjis = Kanji.objects.all()
        total = kanjis.count()
        fixed = 0
        errors = 0

        json_fields = ['compDetail', 'examples']

        for i, kanji in enumerate(kanjis, 1):
            try:
                did_update = False
                for field in json_fields:
                    value = getattr(kanji, field)
                    if isinstance(value, str) and value:
                        try:
                            parsed = json.loads(value)
                            if not dry_run:
                                setattr(kanji, field, parsed)
                            did_update = True
                        except json.JSONDecodeError:
                            pass

                if did_update:
                    if not dry_run:
                        kanji.save()
                    fixed += 1
                    if fixed <= 5:
                        self.stdout.write(f"  Fixed: {kanji.kanji}")

                if i % 500 == 0:
                    self.stdout.write(f"Processed {i}/{total}...")

            except Exception as e:
                self.stderr.write(f"  Error for {kanji.kanji}: {e}")
                errors += 1

        mode = "DRY RUN" if dry_run else "COMPLETE"
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode}!\n"
            f"  Fixed: {fixed}\n"
            f"  Errors: {errors}"
        ))
