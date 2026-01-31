"""
Management command to import book set data from JSON files.
Imports book_set, book_set_unit, and book_set_unit_detail.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.learning.models import (
    BookSet,
    BookSetUnit,
    BookSetUnitDetail,
)


class Command(BaseCommand):
    help = 'Import book set data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )

    def handle(self, *args, **options):
        data_dir = Path('data')

        if options['clear']:
            self.stdout.write('Clearing existing book set data...')
            BookSetUnitDetail.objects.all().delete()
            BookSetUnit.objects.all().delete()
            BookSet.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all book set data'))

        # Import book_set
        book_set_file = data_dir / 'book_set.json'
        if book_set_file.exists():
            self.import_book_sets(book_set_file)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {book_set_file}'))

        # Import book_set_unit
        book_set_unit_file = data_dir / 'book_set_unit.json'
        if book_set_unit_file.exists():
            self.import_book_set_units(book_set_unit_file)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {book_set_unit_file}'))

        # Import book_set_unit_detail
        book_set_unit_detail_file = data_dir / 'book_set_unit_detail.json'
        if book_set_unit_detail_file.exists():
            self.import_book_set_unit_details(book_set_unit_detail_file)
        else:
            self.stdout.write(self.style.WARNING(f'File not found: {book_set_unit_detail_file}'))

        self.stdout.write(self.style.SUCCESS('Book set import completed!'))

    def import_book_sets(self, file_path):
        self.stdout.write(f'Importing book sets from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for item in data:
            book_set, created = BookSet.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'name': item.get('name', ''),
                    'level': str(item.get('level', '')),
                    'total_word': str(item.get('total_word', '')),
                    'version': str(item.get('version', '')),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Book sets: {created_count} created, {updated_count} updated'
            )
        )

    def import_book_set_units(self, file_path):
        self.stdout.write(f'Importing book set units from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for item in data:
            unit, created = BookSetUnit.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'book_set_id': str(item.get('book_set_id', '')),
                    'name': item.get('name', ''),
                    'total_word': str(item.get('total_word', '')),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Book set units: {created_count} created, {updated_count} updated'
            )
        )

    def import_book_set_unit_details(self, file_path):
        self.stdout.write(f'Importing book set unit details from {file_path}...')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0

        for item in data:
            BookSetUnitDetail.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'unit_id': str(item.get('unit_id', '')),
                    'word_id': str(item.get('word_id', '')),
                    'sub_word': item.get('sub_word') or '',
                }
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Book set unit details: {created_count} processed'
            )
        )
