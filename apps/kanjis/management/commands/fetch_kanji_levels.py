"""
Management command to fetch JLPT levels for Kanji from Jisho.org API.
"""
import time
import requests
import urllib.parse
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.kanjis.models import Kanji


class Command(BaseCommand):
    help = 'Fetch JLPT levels from Jisho.org for Kanjis with missing level'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of kanjis to process (0 for all)'
        )
        parser.add_argument(
            '--start',
            type=int,
            default=0,
            help='Start index (offset) for processing'
        )
        parser.add_argument(
            '--sleep',
            type=float,
            default=1.0,
            help='Sleep time between requests in seconds'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        start = options['start']
        sleep_time = options['sleep']

        # Filter kanjis with missing level (null)
        kanjis_qs = Kanji.objects.filter(Q(level__isnull=True) | Q(level=0))

        total_missing = kanjis_qs.count()
        self.stdout.write(f"Found {total_missing} kanjis with missing level.")

        if limit > 0:
            kanjis = kanjis_qs[start:start+limit]
            self.stdout.write(f"Processing {limit} kanjis starting from index {start}.")
        else:
            kanjis = kanjis_qs[start:]
            if start > 0:
                self.stdout.write(f"Processing kanjis starting from index {start}.")

        total_to_process = len(kanjis)
        count = 0
        updated = 0
        not_found = 0
        errors = 0

        self.stdout.write(f"Starting fetch process for {total_to_process} kanjis...")

        for kanji_obj in kanjis:
            count += 1
            char = kanji_obj.kanji

            try:
                # Log progress
                self.stdout.write(f"[{count}/{total_to_process}] Fetching level for: {char}...", ending='')

                if not char:
                    self.stdout.write(self.style.WARNING(" EMPTY CHAR"))
                    skipped_count += 1
                    continue

                # Call Jisho API
                # Note: search/words works for single kanji too
                url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(char)}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('data') and len(data['data']) > 0:
                        # Find matching entry
                        entry = data['data'][0]

                        # Check JLPT field
                        jlpt_levels = entry.get('jlpt', [])

                        if jlpt_levels:
                            # Parse level string "jlpt-n5" -> Integer 5
                            found_level = None
                            for tag in jlpt_levels:
                                if tag.startswith('jlpt-n'):
                                    try:
                                        found_level = int(tag.split('-')[1][1:]) # "jlpt-n5" -> "n5" -> "5" -> 5
                                        break
                                    except (IndexError, ValueError):
                                        continue

                            if found_level:
                                kanji_obj.level = found_level
                                kanji_obj.save()
                                updated += 1
                                self.stdout.write(self.style.SUCCESS(f" FOUND N{found_level}"))
                            else:
                                self.stdout.write(self.style.WARNING(" NO LEVEL TAG"))
                                not_found += 1
                        else:
                            self.stdout.write(self.style.WARNING(" NO JLPT DATA"))
                            not_found += 1
                    else:
                        self.stdout.write(self.style.WARNING(" NOT FOUND"))
                        not_found += 1
                else:
                    self.stdout.write(self.style.ERROR(f" API ERROR {response.status_code}"))
                    errors += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" EXCEPTION: {str(e)}"))
                errors += 1

            # Sleep to be polite
            time.sleep(sleep_time)

        self.stdout.write(self.style.SUCCESS(f"\nDone! Processed: {count}. Updated: {updated}. Not Found/No Level: {not_found}. Errors: {errors}"))
