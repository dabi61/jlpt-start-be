"""
Anki-like spaced repetition helpers for unit learning.
"""
from datetime import timedelta

from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from apps.grammar.models import Grammar
from apps.grammar.serializers import GrammarSerializer
from apps.kanjis.models import Kanji
from apps.kanjis.serializers import KanjiSerializer
from apps.vocabulary.models import Word
from apps.vocabulary.serializers import WordSerializer

from .models import (
    UnitAnkiCard,
    UnitAnkiReviewLog,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UnitWordDetail,
)

LEARNING_STEPS_MINUTES = [1, 10]
RELEARNING_STEPS_MINUTES = [10]
GRADUATING_INTERVAL_DAYS = 1
EASY_INTERVAL_DAYS = 4
HARD_INTERVAL_FACTOR = 1.2
EASY_BONUS = 1.3
AGAIN_REVIEW_INTERVAL_FACTOR = 0.5
MIN_EASE_FACTOR = 1.3


def _numeric_ids(raw_ids):
    """Normalize IDs to digit-only strings and keep stable order."""
    seen = set()
    normalized = []
    for raw in raw_ids:
        value = str(raw or '').strip()
        if not value or not value.isdigit() or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _round_ease(value):
    return round(max(float(value), MIN_EASE_FACTOR), 2)


def _learning_step_due(step_index, now):
    idx = min(max(step_index, 0), len(LEARNING_STEPS_MINUTES) - 1)
    return now + timedelta(minutes=LEARNING_STEPS_MINUTES[idx])


def _relearning_step_due(step_index, now):
    idx = min(max(step_index, 0), len(RELEARNING_STEPS_MINUTES) - 1)
    return now + timedelta(minutes=RELEARNING_STEPS_MINUTES[idx])


def _graduate_to_review(card, now, interval_days):
    card.state = UnitAnkiCard.CardState.REVIEW
    card.step_index = 0
    card.interval_days = max(int(interval_days), 1)
    card.due_at = now + timedelta(days=card.interval_days)


def get_unit_item_refs(unit):
    """
    Return list of tuples: (item_type, item_id) from the unit link tables.
    """
    unit_id = str(unit.id)
    refs = []

    def _append_vocab():
        ids = _numeric_ids(
            UnitWordDetail.objects.filter(unit_id=unit_id).values_list('word_id', flat=True)
        )
        refs.extend((UnitAnkiCard.ItemType.VOCABULARY, item_id) for item_id in ids)

    def _append_grammar():
        ids = _numeric_ids(
            UnitGrammarDetail.objects.filter(unit_id=unit_id).values_list('grammar_id', flat=True)
        )
        refs.extend((UnitAnkiCard.ItemType.GRAMMAR, item_id) for item_id in ids)

    def _append_kanji():
        ids = _numeric_ids(
            UnitKanjiDetail.objects.filter(unit_id=unit_id).values_list('kanji_id', flat=True)
        )
        refs.extend((UnitAnkiCard.ItemType.KANJI, item_id) for item_id in ids)

    if unit.unit_type in ('vocabulary', 'word'):
        _append_vocab()
    elif unit.unit_type == 'grammar':
        _append_grammar()
    elif unit.unit_type == 'kanji':
        _append_kanji()
    else:
        _append_vocab()
        _append_grammar()
        _append_kanji()

    # Fallback for inconsistent unit_type value.
    if not refs:
        _append_vocab()
        _append_grammar()
        _append_kanji()

    return refs


def ensure_unit_cards_for_user(unit, user_id):
    """
    Ensure each linked item in unit has one per-user anki card.
    """
    unit_id = str(unit.id)
    user_id = str(user_id)
    item_refs = get_unit_item_refs(unit)
    if not item_refs:
        return {'total_items': 0, 'created_cards': 0}

    existing_refs = set(
        UnitAnkiCard.objects.filter(user_id=user_id, unit_id=unit_id).values_list('item_type', 'item_id')
    )
    now = timezone.now()
    missing = [
        UnitAnkiCard(
            unit_id=unit_id,
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            due_at=now,
        )
        for item_type, item_id in item_refs
        if (item_type, item_id) not in existing_refs
    ]

    if missing:
        UnitAnkiCard.objects.bulk_create(missing, batch_size=1000, ignore_conflicts=True)

    return {'total_items': len(item_refs), 'created_cards': len(missing)}


def _card_priority():
    return Case(
        When(state=UnitAnkiCard.CardState.LEARNING, then=Value(0)),
        When(state=UnitAnkiCard.CardState.RELEARNING, then=Value(1)),
        When(state=UnitAnkiCard.CardState.REVIEW, then=Value(2)),
        When(state=UnitAnkiCard.CardState.NEW, then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )


def get_next_card(unit_id, user_id, now=None, include_future=True):
    """
    Return next due card. If no due card and include_future=True, return nearest upcoming card.
    """
    now = now or timezone.now()
    base_qs = UnitAnkiCard.objects.filter(unit_id=str(unit_id), user_id=str(user_id))
    due_qs = (
        base_qs
        .filter(due_at__lte=now)
        .annotate(priority=_card_priority())
        .order_by('priority', 'due_at', 'id')
    )
    card = due_qs.first()
    if card:
        return card, True

    if not include_future:
        return None, False

    upcoming = (
        base_qs
        .annotate(priority=_card_priority())
        .order_by('due_at', 'priority', 'id')
        .first()
    )
    return upcoming, False


def get_unit_card_stats(unit_id, user_id, now=None):
    now = now or timezone.now()
    qs = UnitAnkiCard.objects.filter(unit_id=str(unit_id), user_id=str(user_id))
    next_due_at = qs.filter(due_at__gt=now).order_by('due_at').values_list('due_at', flat=True).first()
    return {
        'total_cards': qs.count(),
        'due_now': qs.filter(due_at__lte=now).count(),
        'new_cards': qs.filter(state=UnitAnkiCard.CardState.NEW).count(),
        'learning_cards': qs.filter(state=UnitAnkiCard.CardState.LEARNING).count(),
        'relearning_cards': qs.filter(state=UnitAnkiCard.CardState.RELEARNING).count(),
        'review_cards': qs.filter(state=UnitAnkiCard.CardState.REVIEW).count(),
        'next_due_at': next_due_at,
    }


def _serialize_item(item_type, item_id):
    if not str(item_id).isdigit():
        return None

    int_id = int(item_id)
    if item_type == UnitAnkiCard.ItemType.VOCABULARY:
        item = Word.objects.filter(id=int_id).first()
        return WordSerializer(item).data if item else None
    if item_type == UnitAnkiCard.ItemType.GRAMMAR:
        item = Grammar.objects.filter(id=int_id).first()
        return GrammarSerializer(item).data if item else None
    if item_type == UnitAnkiCard.ItemType.KANJI:
        item = Kanji.objects.filter(id=int_id).first()
        return KanjiSerializer(item).data if item else None
    return None


def serialize_card(card):
    if card is None:
        return None
    return {
        'card_id': card.id,
        'unit_id': card.unit_id,
        'item_type': card.item_type,
        'item_id': card.item_id,
        'state': card.state,
        'step_index': card.step_index,
        'interval_days': card.interval_days,
        'ease_factor': card.ease_factor,
        'reps': card.reps,
        'lapses': card.lapses,
        'due_at': card.due_at,
        'last_reviewed_at': card.last_reviewed_at,
        'content': _serialize_item(card.item_type, card.item_id),
    }


def apply_anki_review(card, rating, response_time_ms=None, now=None):
    """
    Apply an Anki-like SM-2 transition to one card and persist both card and log.
    """
    now = now or timezone.now()
    previous_state = card.state
    previous_interval_days = card.interval_days or 0
    previous_ease_factor = float(card.ease_factor or 2.5)

    card.reps = (card.reps or 0) + 1

    if rating == UnitAnkiReviewLog.Rating.AGAIN:
        if card.state == UnitAnkiCard.CardState.REVIEW:
            card.lapses = (card.lapses or 0) + 1
            card.interval_days = max(1, int(round(max(1, card.interval_days) * AGAIN_REVIEW_INTERVAL_FACTOR)))
            card.ease_factor = _round_ease(card.ease_factor - 0.20)
            card.state = UnitAnkiCard.CardState.RELEARNING
            card.step_index = 0
            card.due_at = _relearning_step_due(0, now)
        elif card.state == UnitAnkiCard.CardState.RELEARNING:
            card.step_index = 0
            card.due_at = _relearning_step_due(0, now)
        else:
            card.state = UnitAnkiCard.CardState.LEARNING
            card.step_index = 0
            card.due_at = _learning_step_due(0, now)

    elif rating == UnitAnkiReviewLog.Rating.HARD:
        if card.state in (UnitAnkiCard.CardState.NEW, UnitAnkiCard.CardState.LEARNING):
            card.state = UnitAnkiCard.CardState.LEARNING
            card.step_index = min(card.step_index + 1, len(LEARNING_STEPS_MINUTES) - 1)
            card.due_at = _learning_step_due(card.step_index, now)
        elif card.state == UnitAnkiCard.CardState.RELEARNING:
            card.step_index = min(card.step_index + 1, len(RELEARNING_STEPS_MINUTES) - 1)
            card.due_at = _relearning_step_due(card.step_index, now)
        else:
            prev = max(1, card.interval_days)
            card.interval_days = max(prev + 1, int(round(prev * HARD_INTERVAL_FACTOR)))
            card.ease_factor = _round_ease(card.ease_factor - 0.15)
            card.due_at = now + timedelta(days=card.interval_days)

    elif rating == UnitAnkiReviewLog.Rating.GOOD:
        if card.state in (UnitAnkiCard.CardState.NEW, UnitAnkiCard.CardState.LEARNING):
            card.state = UnitAnkiCard.CardState.LEARNING
            if card.step_index < len(LEARNING_STEPS_MINUTES) - 1:
                card.step_index += 1
                card.due_at = _learning_step_due(card.step_index, now)
            else:
                next_interval = card.interval_days or GRADUATING_INTERVAL_DAYS
                _graduate_to_review(card, now, next_interval)
        elif card.state == UnitAnkiCard.CardState.RELEARNING:
            if card.step_index < len(RELEARNING_STEPS_MINUTES) - 1:
                card.step_index += 1
                card.due_at = _relearning_step_due(card.step_index, now)
            else:
                next_interval = card.interval_days or GRADUATING_INTERVAL_DAYS
                _graduate_to_review(card, now, next_interval)
        else:
            prev = max(1, card.interval_days)
            card.interval_days = max(prev + 1, int(round(prev * max(card.ease_factor, MIN_EASE_FACTOR))))
            card.due_at = now + timedelta(days=card.interval_days)

    elif rating == UnitAnkiReviewLog.Rating.EASY:
        card.ease_factor = _round_ease(card.ease_factor + 0.15)
        if card.state in (UnitAnkiCard.CardState.NEW, UnitAnkiCard.CardState.LEARNING):
            next_interval = max(EASY_INTERVAL_DAYS, card.interval_days or EASY_INTERVAL_DAYS)
            _graduate_to_review(card, now, next_interval)
        elif card.state == UnitAnkiCard.CardState.RELEARNING:
            prev = max(1, card.interval_days)
            next_interval = max(2, int(round(prev * EASY_BONUS)))
            _graduate_to_review(card, now, next_interval)
        else:
            prev = max(1, card.interval_days)
            card.interval_days = max(
                prev + 1,
                int(round(prev * max(card.ease_factor, MIN_EASE_FACTOR) * EASY_BONUS)),
            )
            card.due_at = now + timedelta(days=card.interval_days)
    else:
        raise ValueError('Unsupported rating value.')

    card.last_reviewed_at = now
    card.save(
        update_fields=[
            'state',
            'step_index',
            'interval_days',
            'ease_factor',
            'reps',
            'lapses',
            'due_at',
            'last_reviewed_at',
            'updated_at',
        ]
    )

    UnitAnkiReviewLog.objects.create(
        card=card,
        rating=rating,
        previous_state=previous_state,
        next_state=card.state,
        previous_interval_days=previous_interval_days,
        next_interval_days=card.interval_days,
        previous_ease_factor=previous_ease_factor,
        next_ease_factor=card.ease_factor,
        response_time_ms=response_time_ms,
    )

    return card
