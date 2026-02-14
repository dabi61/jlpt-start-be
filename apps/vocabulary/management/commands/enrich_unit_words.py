"""
Backfill vocabulary fields for words linked to a unit range.

Primary sources:
- Kanji table: derive `han`, `grid`, and fallback `mean`
- Example table: attach up to N example IDs to `mean[*].examples`
"""
import re
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.examples.models import Example
from apps.kanjis.models import Kanji
from apps.learning.models import Lesson, Unit, UnitWordDetail
from apps.vocabulary.models import Word


JP_TOKEN_RE = re.compile(r'[一-龯ぁ-ゔァ-ヴー々〆〤]+')


class Command(BaseCommand):
    help = 'Enrich words in a unit range with data from kanji/examples tables'

    def add_arguments(self, parser):
        parser.add_argument('--unit-from', type=int, default=1, help='Start unit id (inclusive)')
        parser.add_argument('--unit-to', type=int, default=60, help='End unit id (inclusive)')
        parser.add_argument('--default-level', type=str, default='N5', help='Fallback level when unit/lesson has no level')
        parser.add_argument('--example-limit', type=int, default=10, help='Max example IDs per word')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    @staticmethod
    def _is_blank(value):
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        return False

    @staticmethod
    def _extract_tokens(text):
        if not text:
            return []
        tokens = JP_TOKEN_RE.findall(text)
        # Stable unique by length desc then first seen.
        seen = set()
        ordered = []
        for token in sorted(tokens, key=len, reverse=True):
            if token not in seen:
                seen.add(token)
                ordered.append(token)
        return ordered

    @staticmethod
    def _extract_kanji_chars(text, kanji_lookup):
        chars = []
        seen = set()
        for ch in text or '':
            if ch in kanji_lookup and ch not in seen:
                seen.add(ch)
                chars.append(ch)
        return chars

    @staticmethod
    def _extract_existing_example_ids(mean_value):
        if not isinstance(mean_value, list):
            return []
        ids = []
        for item in mean_value:
            if not isinstance(item, dict):
                continue
            for raw in item.get('examples') or []:
                if isinstance(raw, int):
                    ids.append(raw)
                elif isinstance(raw, str) and raw.isdigit():
                    ids.append(int(raw))
        # unique order
        seen = set()
        out = []
        for eid in ids:
            if eid not in seen:
                seen.add(eid)
                out.append(eid)
        return out

    def _find_example_ids(
        self,
        word,
        example_limit,
        content_cache,
        trans_cache,
    ):
        ids = []
        seen = set()

        def add_ids(candidates):
            for eid in candidates:
                if eid in seen:
                    continue
                seen.add(eid)
                ids.append(eid)
                if len(ids) >= example_limit:
                    return True
            return False

        content_terms = [t for t in self._extract_tokens(word.j_word) if len(t) >= 2]
        for term in content_terms:
            if term not in content_cache:
                content_cache[term] = list(
                    Example.objects.filter(content__contains=term)
                    .order_by('id')
                    .values_list('id', flat=True)[: example_limit * 2]
                )
            if add_ids(content_cache[term]):
                return ids[:example_limit]

        # Fallback: reading-based search on transliteration field.
        trans_terms = [t for t in self._extract_tokens(word.phonetic) if len(t) >= 2]
        for term in trans_terms:
            if term not in trans_cache:
                trans_cache[term] = list(
                    Example.objects.filter(trans__contains=term)
                    .order_by('id')
                    .values_list('id', flat=True)[: example_limit * 2]
                )
            if add_ids(trans_cache[term]):
                return ids[:example_limit]

        return ids[:example_limit]

    def handle(self, *args, **options):
        unit_from = options['unit_from']
        unit_to = options['unit_to']
        default_level = options['default_level']
        example_limit = options['example_limit']
        dry_run = options['dry_run']

        self.stdout.write(
            f'Loading words from units {unit_from}..{unit_to} '
            f'(default_level={default_level}, example_limit={example_limit})'
        )

        units = list(
            Unit.objects.filter(id__gte=unit_from, id__lte=unit_to)
            .filter(unit_type__in=['word', 'vocabulary'])
            .order_by('id')
        )
        if not units:
            self.stdout.write(self.style.WARNING('No target units found.'))
            return

        lesson_ids = [u.lession_id for u in units if u.lession_id and str(u.lession_id).isdigit()]
        lesson_level_map = {
            str(row['id']): row['level']
            for row in Lesson.objects.filter(id__in=lesson_ids).values('id', 'level')
        }
        unit_level_map = {}
        for unit in units:
            inferred = unit.level or lesson_level_map.get(str(unit.lession_id)) or default_level
            unit_level_map[str(unit.id)] = inferred

        details = list(
            UnitWordDetail.objects.filter(unit_id__in=[str(u.id) for u in units])
            .values('unit_id', 'word_id')
        )
        word_ids = []
        word_level_candidates = defaultdict(list)
        for row in details:
            raw_word_id = row.get('word_id')
            if not str(raw_word_id).isdigit():
                continue
            wid = int(raw_word_id)
            word_ids.append(wid)
            level = unit_level_map.get(str(row.get('unit_id')))
            if level:
                word_level_candidates[wid].append(level)

        unique_word_ids = sorted(set(word_ids))
        words = list(Word.objects.filter(id__in=unique_word_ids).order_by('id'))
        self.stdout.write(f'Found {len(words)} words linked to target units.')

        kanji_lookup = {}
        for row in Kanji.objects.exclude(kanji__isnull=True).exclude(kanji='').values(
            'kanji', 'mean', 'stroke_count'
        ):
            char = (row['kanji'] or '').strip()
            if len(char) != 1:
                continue
            kanji_lookup.setdefault(
                char,
                {
                    'mean': row.get('mean'),
                    'stroke_count': row.get('stroke_count'),
                },
            )

        content_cache = {}
        trans_cache = {}
        stats = defaultdict(int)
        changed_words = 0

        for idx, word in enumerate(words, 1):
            changed = False
            fields_to_update = set()
            chars = self._extract_kanji_chars(word.j_word, kanji_lookup)

            if self._is_blank(word.han) and chars:
                word.han = ''.join(chars)
                fields_to_update.add('han')
                stats['han_filled'] += 1
                changed = True

            if self._is_blank(word.grid) and chars:
                strokes = [
                    int(kanji_lookup[ch]['stroke_count'])
                    for ch in chars
                    if kanji_lookup.get(ch, {}).get('stroke_count')
                ]
                if strokes:
                    word.grid = str(sum(strokes))
                    fields_to_update.add('grid')
                    stats['grid_filled'] += 1
                    changed = True

            if self._is_blank(word.level):
                levels = word_level_candidates.get(word.id, [])
                inferred_level = levels[0] if levels else default_level
                if inferred_level:
                    word.level = inferred_level
                    fields_to_update.add('level')
                    stats['level_filled'] += 1
                    changed = True

            if word.opposite_word is None:
                word.opposite_word = []
                fields_to_update.add('opposite_word')
                stats['opposite_word_filled'] += 1
                changed = True

            if word.synsets is None:
                word.synsets = []
                fields_to_update.add('synsets')
                stats['synsets_filled'] += 1
                changed = True

            if word.related_words is None:
                word.related_words = []
                fields_to_update.add('related_words')
                stats['related_words_filled'] += 1
                changed = True

            existing_example_ids = self._extract_existing_example_ids(word.mean)
            example_ids = existing_example_ids
            if not example_ids:
                example_ids = self._find_example_ids(
                    word=word,
                    example_limit=example_limit,
                    content_cache=content_cache,
                    trans_cache=trans_cache,
                )

            mean_missing = word.mean is None or word.mean == []
            if mean_missing:
                kanji_means = []
                seen = set()
                for ch in chars:
                    raw_mean = (kanji_lookup.get(ch, {}).get('mean') or '').strip()
                    if not raw_mean or raw_mean in seen:
                        continue
                    seen.add(raw_mean)
                    kanji_means.append(raw_mean)

                if kanji_means:
                    word.mean = [
                        {
                            'kind': 'kanji_ref',
                            'mean': '; '.join(kanji_means),
                            'examples': example_ids,
                        }
                    ]
                    fields_to_update.add('mean')
                    stats['mean_filled'] += 1
                    if example_ids:
                        stats['examples_attached'] += 1
                    changed = True
                elif word.mean is None:
                    # Keep contract stable (array) even when we cannot infer meaning text.
                    word.mean = []
                    fields_to_update.add('mean')
                    stats['mean_filled'] += 1
                    changed = True
            elif example_ids and not existing_example_ids and isinstance(word.mean, list):
                attached = False
                for entry in word.mean:
                    if not isinstance(entry, dict):
                        continue
                    if entry.get('examples'):
                        continue
                    entry['examples'] = example_ids
                    attached = True
                    break
                if attached:
                    word.mean = word.mean
                    fields_to_update.add('mean')
                    stats['examples_attached'] += 1
                    changed = True

            if changed:
                changed_words += 1
                if not dry_run:
                    word.save(update_fields=sorted(fields_to_update))

            if idx % 200 == 0:
                self.stdout.write(f'Processed {idx}/{len(words)} words...')

        mode = 'DRY RUN' if dry_run else 'DONE'
        self.stdout.write(self.style.SUCCESS(f'\n{mode}: enriched {changed_words}/{len(words)} words'))
        self.stdout.write(f"  han filled: {stats['han_filled']}")
        self.stdout.write(f"  grid filled: {stats['grid_filled']}")
        self.stdout.write(f"  level filled: {stats['level_filled']}")
        self.stdout.write(f"  mean touched: {stats['mean_filled']}")
        self.stdout.write(f"  examples attached: {stats['examples_attached']}")
        self.stdout.write(f"  opposite_word filled: {stats['opposite_word_filled']}")
        self.stdout.write(f"  synsets filled: {stats['synsets_filled']}")
        self.stdout.write(f"  related_words filled: {stats['related_words_filled']}")
