from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Replace
from django.db.models import Value


@dataclass(frozen=True)
class _Replacement:
    old: str
    new: str


def _public_url_for_key(*, base: str, key: str) -> str:
    safe_key = quote((key or '').lstrip('/'), safe='/')
    return f"{base}/{safe_key}"


def _iter_levels(raw: str) -> list[str]:
    parts = [p.strip().lower() for p in (raw or '').split(',') if p.strip()]
    seen: set[str] = set()
    levels: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            levels.append(p)
    return levels


class Command(BaseCommand):
    help = (
        "Fix stored R2 public URLs by URL-encoding object keys (e.g. files whose "
        "name contains literal '%' like 'a%20b.jpg'). This updates MediaAsset.public_url "
        "and replaces old URLs in question/item text fields."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--levels',
            default='n1,n2,n3,n4,n5',
            help="Comma-separated levels to process (default: n1,n2,n3,n4,n5).",
        )
        parser.add_argument(
            '--base-url',
            default='',
            help="Override R2 public base URL (default: settings.R2_PUBLIC_BASE_URL).",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without writing to the database.',
        )

    def _get_models(self, level: str):
        lvl = level.upper()
        try:
            media = django_apps.get_model(level, f"{lvl}MediaAsset")
            question = django_apps.get_model(level, f"{lvl}Question")
            item = django_apps.get_model(level, f"{lvl}QuestionItem")
        except LookupError as exc:
            raise CommandError(f"Unknown/unsupported level '{level}'.") from exc
        return media, question, item

    def _build_replacements(self, *, base: str, MediaAssetModel) -> list[_Replacement]:
        replacements: list[_Replacement] = []
        for asset in MediaAssetModel.objects.all().only('id', 'public_url', 'r2_key'):
            new_url = _public_url_for_key(base=base, key=asset.r2_key)
            old_url = asset.public_url or ''
            if old_url and old_url != new_url:
                replacements.append(_Replacement(old=old_url, new=new_url))
        return replacements

    def _apply_replacements(
        self,
        *,
        replacements: Iterable[_Replacement],
        QuestionModel,
        QuestionItemModel,
        dry_run: bool,
    ) -> dict[str, int]:
        counts = {
            'questions.general_audio_url': 0,
            'questions.general_image_url': 0,
            'questions.title': 0,
            'questions.general_txt_read': 0,
            'questions.general_text_read_en': 0,
            'questions.general_text_read_vn': 0,
            'items.image_url': 0,
            'items.question_text': 0,
            'items.explain_en': 0,
            'items.explain_vn': 0,
        }

        for rep in replacements:
            # Exact URL fields.
            q = QuestionModel.objects.filter(general_audio_url=rep.old)
            counts['questions.general_audio_url'] += q.count() if dry_run else q.update(general_audio_url=rep.new)

            q = QuestionModel.objects.filter(general_image_url=rep.old)
            counts['questions.general_image_url'] += q.count() if dry_run else q.update(general_image_url=rep.new)

            qi = QuestionItemModel.objects.filter(image_url=rep.old)
            counts['items.image_url'] += qi.count() if dry_run else qi.update(image_url=rep.new)

            # Embedded URLs in text.
            for field_key, model, field_name in (
                ('questions.title', QuestionModel, 'title'),
                ('questions.general_txt_read', QuestionModel, 'general_txt_read'),
                ('questions.general_text_read_en', QuestionModel, 'general_text_read_en'),
                ('questions.general_text_read_vn', QuestionModel, 'general_text_read_vn'),
                ('items.question_text', QuestionItemModel, 'question_text'),
                ('items.explain_en', QuestionItemModel, 'explain_en'),
                ('items.explain_vn', QuestionItemModel, 'explain_vn'),
            ):
                qs = model.objects.filter(**{f"{field_name}__contains": rep.old})
                if dry_run:
                    counts[field_key] += qs.count()
                else:
                    counts[field_key] += qs.update(
                        **{
                            field_name: Replace(
                                F(field_name),
                                Value(rep.old),
                                Value(rep.new),
                            )
                        }
                    )

        return counts

    def handle(self, *args, **options):
        levels = _iter_levels(options.get('levels'))
        if not levels:
            raise CommandError('No levels provided.')

        base_url = (options.get('base_url') or settings.R2_PUBLIC_BASE_URL or '').rstrip('/')
        if not base_url:
            raise CommandError('R2_PUBLIC_BASE_URL is not configured (and --base-url not provided).')

        dry_run = bool(options.get('dry_run'))

        self.stdout.write(f"Base URL: {base_url}")
        self.stdout.write(f"Levels: {', '.join(levels)}")
        if dry_run:
            self.stdout.write('Dry-run: yes (no DB writes)')

        total_assets_updated = 0

        with transaction.atomic():
            for level in levels:
                MediaAssetModel, QuestionModel, QuestionItemModel = self._get_models(level)
                replacements = self._build_replacements(base=base_url, MediaAssetModel=MediaAssetModel)

                if not replacements:
                    self.stdout.write(f"[{level}] No URL changes needed.")
                    continue

                # Update MediaAsset.public_url first.
                assets_to_update = []
                for asset in MediaAssetModel.objects.all().only('id', 'public_url', 'r2_key'):
                    new_url = _public_url_for_key(base=base_url, key=asset.r2_key)
                    if asset.public_url and asset.public_url != new_url:
                        asset.public_url = new_url
                        assets_to_update.append(asset)

                if dry_run:
                    self.stdout.write(f"[{level}] Media assets to update: {len(assets_to_update)}")
                else:
                    MediaAssetModel.objects.bulk_update(assets_to_update, ['public_url'], batch_size=500)
                total_assets_updated += len(assets_to_update)

                counts = self._apply_replacements(
                    replacements=replacements,
                    QuestionModel=QuestionModel,
                    QuestionItemModel=QuestionItemModel,
                    dry_run=dry_run,
                )

                self.stdout.write(
                    f"[{level}] Updated: media_assets={len(assets_to_update)} "
                    f"general_audio_url={counts['questions.general_audio_url']} "
                    f"general_image_url={counts['questions.general_image_url']} "
                    f"item_image_url={counts['items.image_url']} "
                    f"text_fields={sum(v for k, v in counts.items() if k.endswith(('title','general_txt_read','general_text_read_en','general_text_read_vn','question_text','explain_en','explain_vn')))}"
                )

            if dry_run:
                # Keep the transaction open, but no writes should have happened.
                pass

        self.stdout.write(f"Total media assets updated: {total_assets_updated}")

