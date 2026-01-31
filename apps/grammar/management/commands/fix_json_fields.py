"""
Management command to fix JSON fields stored as strings in Grammar model.
"""
import json
from django.core.management.base import BaseCommand
from apps.grammar.models import Grammar


class Command(BaseCommand):
    help = 'Fix JSON fields (examples, synonyms, fun_fact, caution) stored as strings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("Scanning Grammar records with string JSON fields...")

        grammars = Grammar.objects.all()
        total = grammars.count()
        fixed = 0
        errors = 0

        json_fields = ['examples', 'synonyms', 'fun_fact', 'caution']

        for i, grammar in enumerate(grammars, 1):
            try:
                did_update = False
                for field in json_fields:
                    value = getattr(grammar, field)
                    if isinstance(value, str) and value:
                        try:
                            parsed = json.loads(value)
                            if not dry_run:
                                setattr(grammar, field, parsed)
                            did_update = True
                        except json.JSONDecodeError:
                            pass

                if did_update:
                    if not dry_run:
                        grammar.save()
                    fixed += 1
                    if fixed <= 5:
                        self.stdout.write(f"  Fixed: {grammar.title}")

                if i % 200 == 0:
                    self.stdout.write(f"Processed {i}/{total}...")

            except Exception as e:
                self.stderr.write(f"  Error for {grammar.title}: {e}")
                errors += 1

        mode = "DRY RUN" if dry_run else "COMPLETE"
        self.stdout.write(self.style.SUCCESS(
            f"\n{mode}!\n"
            f"  Fixed: {fixed}\n"
            f"  Errors: {errors}"
        ))
