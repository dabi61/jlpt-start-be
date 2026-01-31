"""
Management command to import examples from JSON file.
"""
import json
from django.core.management.base import BaseCommand
from django.db import connection
from apps.examples.models import Example


class Command(BaseCommand):
    help = 'Import example sentences from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing examples if found'
        )
        parser.add_argument(
            '--preserve-ids',
            action='store_true',
            help='Preserve original IDs from JSON file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing examples before import'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        update = options['update']
        preserve_ids = options['preserve_ids']
        clear = options['clear']

        self.stdout.write(f"Loading examples from {json_file}...")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {e}"))
            return

        if not isinstance(data, list):
            data = [data]

        total = len(data)
        self.stdout.write(f"Found {total} examples to import...")

        # Clear existing data if requested
        if clear:
            deleted_count = Example.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing examples."))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, item in enumerate(data, 1):
            try:
                content = item.get('content', '')
                if content is None:
                    content = ''
                content = content.strip()

                if not content:
                    skipped_count += 1
                    continue

                mean = item.get('mean')
                trans = item.get('trans')
                original_id = item.get('id')

                if preserve_ids and original_id:
                    # Check if ID already exists
                    existing = Example.objects.filter(id=original_id).first()
                    if existing:
                        if update:
                            did_update = False
                            if content and existing.content != content:
                                existing.content = content
                                did_update = True
                            if mean and existing.mean != mean:
                                existing.mean = mean
                                did_update = True
                            if trans and existing.trans != trans:
                                existing.trans = trans
                                did_update = True
                            if did_update:
                                existing.save()
                                updated_count += 1
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # Create with specific ID
                        Example.objects.create(
                            id=original_id,
                            content=content,
                            mean=mean,
                            trans=trans
                        )
                        created_count += 1
                else:
                    # Original logic: deduplicate by content
                    existing = Example.objects.filter(content=content).first()
                    if existing:
                        if update:
                            did_update = False
                            if mean and existing.mean != mean:
                                existing.mean = mean
                                did_update = True
                            if trans and existing.trans != trans:
                                existing.trans = trans
                                did_update = True
                            if did_update:
                                existing.save()
                                updated_count += 1
                            else:
                                skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        Example.objects.create(
                            content=content,
                            mean=mean,
                            trans=trans
                        )
                        created_count += 1

                if i % 500 == 0:
                    self.stdout.write(f"Processed {i}/{total} examples...")

            except Exception as e:
                self.stderr.write(f"Error importing example {i}: {str(e)}")
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete!\n"
            f"  Created: {created_count}\n"
            f"  Updated: {updated_count}\n"
            f"  Skipped: {skipped_count}\n"
            f"  Errors:  {error_count}"
        ))

