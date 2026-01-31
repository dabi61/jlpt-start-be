"""
Management command to fetch JLPT levels from Jisho.org API.
"""
import time
import requests
import urllib.parse
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.vocabulary.models import Word


class Command(BaseCommand):
    help = 'Fetch JLPT levels from Jisho.org for words with missing level'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of words to process (0 for all)'
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

        # Filter words with missing level (null or empty)
        words_qs = Word.objects.filter(Q(level__isnull=True) | Q(level=''))

        total_missing = words_qs.count()
        self.stdout.write(f"Found {total_missing} words with missing level.")

        if limit > 0:
            words = words_qs[start:start+limit]
            self.stdout.write(f"Processing {limit} words starting from index {start}.")
        else:
            words = words_qs[start:]
            if start > 0:
                self.stdout.write(f"Processing words starting from index {start}.")

        total_to_process = len(words)
        count = 0
        updated = 0
        not_found = 0
        errors = 0

        self.stdout.write(f"Starting fetch process for {total_to_process} words...")

        for word in words:
            count += 1
            j_word = word.j_word

            try:
                # Log progress
                self.stdout.write(f"[{count}/{total_to_process}] Fetching level for: {j_word}...", ending='')

                # Call Jisho API
                url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(j_word)}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('data') and len(data['data']) > 0:
                        # Find matching entry (exact match preferred)
                        entry = data['data'][0] # Take first result for now

                        # Check JLPT field
                        jlpt_levels = entry.get('jlpt', [])

                        if jlpt_levels:
                            # Format: ["jlpt-n5", "jlpt-n4"]
                            # We take the lowest number (highest level) or just the first one?
                            # Usually usually "jlpt-n5" means it is N5.

                            # Parse level string "jlpt-n5" -> "N5"
                            # Sort key to find "highest" level?
                            # Actually Jisho usually returns the relevant level.
                            # Example: ['jlpt-n3', 'jlpt-n2'] -> It covers both?
                            # Let's take the lowest N-number (highest difficulty) or highest N-number (lowest difficulty)?
                            # N1 is hardest, N5 is easiest.
                            # Usually we want the minimum level required? Or the level bucket it belongs do?
                            # If a word is N5, it is also N4, N3, N2, N1 vocabulary? No.
                            # Let's just take the first one found that matches format.

                            found_level = None
                            for tag in jlpt_levels:
                                if tag.startswith('jlpt-n'):
                                    # tag = "jlpt-n5" -> "n5" -> "N5"
                                    found_level = tag.split('-')[1].upper()
                                    break

                            if found_level:
                                word.level = found_level
                                word.save()
                                updated += 1
                                self.stdout.write(self.style.SUCCESS(f" FOUND {found_level}"))
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
