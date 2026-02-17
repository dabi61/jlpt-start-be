"""Import JLPT N2 dataset from JSON files and upload media to Cloudflare R2."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.n2.models import (
    N2Exam,
    N2MediaAsset,
    N2Question,
    N2QuestionItem,
    N2Section,
    N2Subcategory,
)

MEDIA_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif',
    '.mp3', '.wav', '.m4a', '.ogg',
}
# Only rewrite URLs that look like media assets (avoid fetching random website links in reading text).
MEDIA_URL_RE = re.compile(
    r'https?://[^\s"\'<>]+?\.(?:png|jpe?g|gif|mp3|wav|m4a|ogg)(?:\?[^\s"\'<>]*)?',
    re.IGNORECASE,
)

SECTION_NAME_MAP = {
    'Doc': 'Đọc',
    'Nghe': 'Nghe',
    'NguPhap': 'Ngữ pháp',
    'TuVung': 'Từ vựng',
}

SUBCATEGORY_NAME_MAP = {
    'DoanVanNgan': 'Đoạn văn ngắn',
    'DoanVanTrungBinh': 'Đoạn văn trung bình',
    'DoanVanDai': 'Đoạn văn dài',
    'DocHieuChuDe': 'Đọc hiểu chủ đề',
    'DocHieuTongHop': 'Đọc hiểu tổng hợp',
    'TimThongTin': 'Tìm thông tin',
    'NgheHieuChuDe': 'Nghe hiểu chủ đề',
    'NgheHieuDiemChinh': 'Nghe hiểu điểm chính',
    'NgheHieuKhaiQuat': 'Nghe hiểu khái quát',
    'NgheHieuTongHop': 'Nghe hiểu tổng hợp',
    'NgheHieuDienDat': 'Nghe hiểu diễn đạt',
    'TraLoiNhanh': 'Trả lời nhanh',
    'DangNguPhap': 'Dạng ngữ pháp',
    'NguPhapTheoDoanVan': 'Ngữ pháp theo đoạn văn',
    'ThanhLapCau': 'Thành lập câu',
    'BieuHienTu': 'Biểu hiện từ',
    'CachDocHiragana': 'Cách đọc Hiragana',
    'CachDocKanji': 'Cách đọc Kanji',
    'CachDungTu': 'Cách dùng từ',
    'CauTaoTu': 'Cấu tạo từ',
    'DongNghia': 'Đồng nghĩa',
}


@dataclass
class UploadedMedia:
    public_url: str
    r2_key: str
    content_type: str
    content_length: int


class R2Uploader:
    def __init__(self, prefix: str):
        self.prefix = prefix.strip().strip('/')
        self.endpoint_url = settings.R2_ENDPOINT_URL
        self.region = getattr(settings, 'R2_REGION', 'auto') or 'auto'
        self.bucket = settings.R2_BUCKET_NAME
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self.public_base = (settings.R2_PUBLIC_BASE_URL or '').rstrip('/')

        missing = []
        if not self.endpoint_url:
            missing.append('R2_ENDPOINT_URL')
        if not self.bucket:
            missing.append('R2_BUCKET_NAME')
        if not self.access_key:
            missing.append('R2_ACCESS_KEY_ID')
        if not self.secret_key:
            missing.append('R2_SECRET_ACCESS_KEY')
        if not self.public_base:
            missing.append('R2_PUBLIC_BASE_URL')
        if missing:
            raise CommandError(f"Missing R2 settings: {', '.join(missing)}")

        cfg = Config(signature_version='s3v4', s3={'addressing_style': 'path'})
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=cfg,
        )

    def build_key(self, basename: str, remote: bool = False, source_url: str = '') -> str:
        safe_basename = os.path.basename(basename)
        if remote:
            digest = hashlib.sha1(source_url.encode('utf-8')).hexdigest()[:16]
            return f"{self.prefix}/remote/{digest}_{safe_basename}"
        return f"{self.prefix}/{safe_basename}"

    def build_public_url(self, key: str) -> str:
        # URL-encode the key path but keep slashes, so filenames like `a%20b.jpg` remain accessible.
        safe_key = quote(key.lstrip('/'), safe='/')
        return f"{self.public_base}/{safe_key}"

    def _guess_content_type(self, filename: str) -> str:
        ct, _ = mimetypes.guess_type(filename)
        return ct or 'application/octet-stream'

    def upload_local_file(self, local_path: Path, key: str) -> UploadedMedia:
        content_type = self._guess_content_type(local_path.name)
        content_length = int(local_path.stat().st_size)
        try:
            with local_path.open('rb') as f:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=f,
                    ContentType=content_type,
                    CacheControl='public, max-age=31536000, immutable',
                )
        except (BotoCoreError, ClientError) as exc:
            raise CommandError(f"Failed uploading local media '{local_path}': {exc}") from exc

        return UploadedMedia(
            public_url=self.build_public_url(key),
            r2_key=key,
            content_type=content_type,
            content_length=content_length,
        )

    def upload_remote_bytes(self, source_url: str, data: bytes, basename: str, content_type: str = '') -> UploadedMedia:
        guessed = content_type or self._guess_content_type(basename)
        key = self.build_key(basename=basename, remote=True, source_url=source_url)
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=guessed,
                CacheControl='public, max-age=31536000, immutable',
            )
        except (BotoCoreError, ClientError) as exc:
            raise CommandError(f"Failed uploading remote media '{source_url}': {exc}") from exc

        return UploadedMedia(
            public_url=self.build_public_url(key),
            r2_key=key,
            content_type=guessed,
            content_length=len(data),
        )


class Command(BaseCommand):
    help = 'Import N2 JSON dataset, upload media to R2, and map media URLs into question data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-dir',
            type=str,
            default='n2',
            help='Source directory containing N2 JSON and media folders (default: n2).',
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='n2/images',
            help='R2 key prefix for uploaded media (default: n2/images).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing N2 tables before importing.',
        )
        parser.add_argument(
            '--skip-upload-local',
            action='store_true',
            help='Skip uploading local media files from source-dir.',
        )
        parser.add_argument(
            '--skip-upload-remote',
            action='store_true',
            help='Do not fetch/upload unresolved remote media URLs from JSON.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and report only, do not write DB/upload media.',
        )
        parser.add_argument(
            '--skip-existing-exams',
            action='store_true',
            help='Skip JSON files whose exam (source_file) already exists in DB.',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['source_dir']).resolve()
        prefix = options['prefix']
        clear = bool(options['clear'])
        skip_upload_local = bool(options['skip_upload_local'])
        skip_upload_remote = bool(options['skip_upload_remote'])
        dry_run = bool(options['dry_run'])
        skip_existing_exams = bool(options.get('skip_existing_exams'))

        if not source_dir.exists() or not source_dir.is_dir():
            raise CommandError(f"Source dir not found: {source_dir}")

        json_files = sorted(source_dir.rglob('*.json'))
        if not json_files:
            raise CommandError(f"No JSON files found under: {source_dir}")

        self.stdout.write(self.style.NOTICE(f"Found {len(json_files)} JSON files."))

        uploader = None
        if not dry_run:
            uploader = R2Uploader(prefix=prefix)

        local_media_map: dict[str, UploadedMedia] = {}
        local_variant_map: dict[str, set[str]] = {}
        # Cache remote URLs -> mapped public URLs to avoid re-downloading/uploading.
        # Useful when re-running the import after media has already been uploaded.
        remote_url_cache: dict[str, str] = {}
        if not dry_run:
            remote_url_cache = self._load_remote_url_cache()

        if clear and not dry_run:
            self.stdout.write(self.style.WARNING('Clearing existing N2 dataset...'))
            self._clear_existing_data()

        if not skip_upload_local:
            local_media_map, local_variant_map = self._upload_local_media(
                source_dir=source_dir,
                uploader=uploader,
                dry_run=dry_run,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Local media prepared: {len(local_media_map)} files ({'dry-run' if dry_run else 'uploaded'})."
            ))
        else:
            local_media_map, local_variant_map = self._build_local_media_indices(source_dir, uploader=uploader)
            self.stdout.write(self.style.WARNING('Skipped local media upload; using local index for mapping only.'))

        summary = {
            'files': 0,
            'exam_created': 0,
            'exam_updated': 0,
            'questions_created': 0,
            'questions_updated': 0,
            'items_created': 0,
            'items_updated': 0,
            'mapped_local_urls': 0,
            'mapped_remote_urls': 0,
            'unresolved_urls': 0,
        }

        for json_path in json_files:
            relative = json_path.relative_to(source_dir)
            if skip_existing_exams and not dry_run:
                if N2Exam.objects.filter(source_file=str(relative)).exists():
                    self.stdout.write(f"Skipping {relative} (already imported).")
                    continue

            self.stdout.write(f"Importing {relative} ...")
            file_stats = self._import_one_json(
                source_dir=source_dir,
                json_path=json_path,
                local_media_map=local_media_map,
                local_variant_map=local_variant_map,
                remote_url_cache=remote_url_cache,
                uploader=uploader,
                skip_upload_remote=skip_upload_remote,
                dry_run=dry_run,
            )
            summary['files'] += 1
            for key, value in file_stats.items():
                summary[key] = summary.get(key, 0) + value

        self.stdout.write(self.style.SUCCESS('N2 import finished.'))
        for key in sorted(summary.keys()):
            self.stdout.write(f"  {key}: {summary[key]}")

    def _clear_existing_data(self):
        N2Section.objects.all().delete()
        N2MediaAsset.objects.all().delete()

    def _load_remote_url_cache(self) -> dict[str, str]:
        """Build a cache mapping remote source URLs to already-uploaded public URLs."""
        cache: dict[str, str] = {}
        for source_url, public_url in (
            N2MediaAsset.objects
            .filter(source_type=N2MediaAsset.SourceType.REMOTE)
            .exclude(source_url='')
            .exclude(public_url='')
            .values_list('source_url', 'public_url')
        ):
            if source_url and public_url:
                cache[str(source_url)] = str(public_url)
        return cache

    def _build_local_media_indices(
        self,
        source_dir: Path,
        uploader: R2Uploader | None = None,
    ) -> tuple[dict[str, UploadedMedia], dict[str, set[str]]]:
        media_map: dict[str, UploadedMedia] = {}
        variant_map: dict[str, set[str]] = {}

        for path in source_dir.rglob('*'):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext not in MEDIA_EXTENSIONS:
                continue

            basename = path.name
            public_url = ''
            r2_key = ''
            if uploader is not None:
                # Build deterministic URLs for already-uploaded objects.
                # This enables fast re-import without re-uploading large media sets.
                r2_key = uploader.build_key(basename=basename, remote=False)
                public_url = uploader.build_public_url(r2_key)
            uploaded = UploadedMedia(
                public_url=public_url,
                r2_key=r2_key,
                content_type=mimetypes.guess_type(basename)[0] or 'application/octet-stream',
                content_length=int(path.stat().st_size),
            )
            media_map[basename] = uploaded
            for variant in self._build_variants(basename):
                variant_map.setdefault(variant, set()).add(basename)

            if uploader is not None:
                # Keep MediaAsset table consistent even when skipping uploads.
                media_type = self._detect_media_type(ext)
                rel_path = str(path.relative_to(source_dir))
                self._upsert_media_asset(
                    source_type=N2MediaAsset.SourceType.LOCAL,
                    media_type=media_type,
                    source_url='',
                    source_path=rel_path,
                    source_basename=basename,
                    uploaded=uploaded,
                    metadata={'source_dir': str(source_dir.name), 'skip_upload_local': True},
                )

        return media_map, variant_map

    def _upload_local_media(
        self,
        *,
        source_dir: Path,
        uploader: R2Uploader | None,
        dry_run: bool,
    ) -> tuple[dict[str, UploadedMedia], dict[str, set[str]]]:
        media_map: dict[str, UploadedMedia] = {}
        variant_map: dict[str, set[str]] = {}

        media_files: list[Path] = []
        for path in source_dir.rglob('*'):
            if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS:
                media_files.append(path)

        for idx, path in enumerate(sorted(media_files), 1):
            basename = path.name
            for variant in self._build_variants(basename):
                variant_map.setdefault(variant, set()).add(basename)

            if dry_run:
                media = UploadedMedia(
                    public_url='',
                    r2_key='',
                    content_type=mimetypes.guess_type(basename)[0] or 'application/octet-stream',
                    content_length=int(path.stat().st_size),
                )
            else:
                assert uploader is not None
                key = uploader.build_key(basename=basename, remote=False)
                media = uploader.upload_local_file(local_path=path, key=key)

                media_type = self._detect_media_type(path.suffix)
                rel_path = str(path.relative_to(source_dir))
                self._upsert_media_asset(
                    source_type=N2MediaAsset.SourceType.LOCAL,
                    media_type=media_type,
                    source_url='',
                    source_path=rel_path,
                    source_basename=basename,
                    uploaded=media,
                    metadata={'source_dir': str(source_dir.name)},
                )

            media_map[basename] = media

            if idx % 200 == 0:
                self.stdout.write(f"  processed local media {idx}/{len(media_files)}")

        return media_map, variant_map

    @staticmethod
    def _build_variants(basename: str) -> list[str]:
        variants = {basename}

        variant = basename
        for _ in range(4):
            stripped = re.sub(r'^\d+_', '', variant)
            if stripped == variant:
                break
            variants.add(stripped)
            variant = stripped

        root, ext = os.path.splitext(variant)
        if root.endswith('_fixed'):
            variants.add(f"{root[:-6]}{ext}")
        else:
            variants.add(f"{root}_fixed{ext}")

        return sorted(variants)

    @staticmethod
    def _detect_media_type(ext: str) -> str:
        ext = ext.lower()
        if ext in {'.png', '.jpg', '.jpeg', '.gif'}:
            return N2MediaAsset.MediaType.IMAGE
        if ext in {'.mp3', '.wav', '.m4a', '.ogg'}:
            return N2MediaAsset.MediaType.AUDIO
        return N2MediaAsset.MediaType.OTHER

    def _upsert_media_asset(
        self,
        *,
        source_type: str,
        media_type: str,
        source_url: str,
        source_path: str,
        source_basename: str,
        uploaded: UploadedMedia,
        metadata: dict[str, Any] | None = None,
    ):
        N2MediaAsset.objects.update_or_create(
            r2_key=uploaded.r2_key,
            defaults={
                'source_type': source_type,
                'media_type': media_type,
                'source_url': source_url,
                'source_path': source_path,
                'source_basename': source_basename,
                'public_url': uploaded.public_url,
                'content_type': uploaded.content_type,
                'content_length': uploaded.content_length,
                'metadata': metadata or {},
            },
        )

    def _import_one_json(
        self,
        *,
        source_dir: Path,
        json_path: Path,
        local_media_map: dict[str, UploadedMedia],
        local_variant_map: dict[str, set[str]],
        remote_url_cache: dict[str, str],
        uploader: R2Uploader | None,
        skip_upload_remote: bool,
        dry_run: bool,
    ) -> dict[str, int]:
        relative = json_path.relative_to(source_dir)
        parts = relative.parts
        if len(parts) < 3:
            raise CommandError(f"Unexpected JSON path structure: {relative}")

        section_key, subcategory_key = parts[0], parts[1]
        section_name = SECTION_NAME_MAP.get(section_key, section_key)
        sub_name = SUBCATEGORY_NAME_MAP.get(subcategory_key, subcategory_key)

        try:
            payload = json.loads(json_path.read_text(encoding='utf-8'))
        except Exception as exc:
            raise CommandError(f"Failed to parse {relative}: {exc}") from exc

        root = (payload or {}).get('Questions') or {}
        time_limit = int(root.get('Time') or 0)
        rows = root.get('Questions') or []

        if not isinstance(rows, list):
            raise CommandError(f"Questions.Questions is not a list in {relative}")

        source_kind = ''
        exam_slug = slugify(json_path.stem)
        exam_name = f"{sub_name} - {json_path.stem}"
        if rows and isinstance(rows[0], dict):
            source_kind = str(rows[0].get('kind') or '').strip()

        dataset_level = 3
        if rows and isinstance(rows[0], dict):
            try:
                dataset_level = int(rows[0].get('level') or 2)
            except (TypeError, ValueError):
                dataset_level = 3

        stats = {
            'exam_created': 0,
            'exam_updated': 0,
            'questions_created': 0,
            'questions_updated': 0,
            'items_created': 0,
            'items_updated': 0,
            'mapped_local_urls': 0,
            'mapped_remote_urls': 0,
            'unresolved_urls': 0,
        }

        if dry_run:
            return stats

        assert uploader is not None

        with transaction.atomic():
            section, _ = N2Section.objects.get_or_create(
                code=slugify(section_key),
                defaults={
                    'name': section_name,
                    'sort_order': self._section_sort_order(section_key),
                },
            )
            if section.name != section_name:
                section.name = section_name
                section.save(update_fields=['name', 'updated_at'])

            subcategory, _ = N2Subcategory.objects.get_or_create(
                section=section,
                code=slugify(subcategory_key),
                defaults={
                    'source_key': subcategory_key,
                    'name': sub_name,
                    'sort_order': self._subcategory_sort_order(section_key, subcategory_key),
                },
            )
            changed = False
            if subcategory.source_key != subcategory_key:
                subcategory.source_key = subcategory_key
                changed = True
            if subcategory.name != sub_name:
                subcategory.name = sub_name
                changed = True
            if changed:
                subcategory.save(update_fields=['source_key', 'name', 'updated_at'])

            exam, created = N2Exam.objects.update_or_create(
                source_file=str(relative),
                defaults={
                    'subcategory': subcategory,
                    'slug': exam_slug,
                    'name': exam_name,
                    'source_kind': source_kind,
                    'jlpt_level': dataset_level,
                    'time_limit_seconds': time_limit,
                    'question_count': len(rows),
                    'metadata': {'source_json': str(relative)},
                },
            )
            if created:
                stats['exam_created'] += 1
            else:
                stats['exam_updated'] += 1

            for order, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue

                source_id = int(row.get('id') or 0)
                if not source_id:
                    continue

                general = row.get('general') if isinstance(row.get('general'), dict) else {}
                mapped_general_audio, hit_type = self._map_media_value(
                    value=str(general.get('audio') or ''),
                    source_json_relative=str(relative),
                    local_media_map=local_media_map,
                    local_variant_map=local_variant_map,
                    remote_url_cache=remote_url_cache,
                    uploader=uploader,
                    skip_upload_remote=skip_upload_remote,
                )
                stats[f'mapped_{hit_type}_urls' if hit_type in ('local', 'remote') else 'unresolved_urls'] += 1 if hit_type else 0

                mapped_general_image, hit_type = self._map_media_value(
                    value=str(general.get('image') or ''),
                    source_json_relative=str(relative),
                    local_media_map=local_media_map,
                    local_variant_map=local_variant_map,
                    remote_url_cache=remote_url_cache,
                    uploader=uploader,
                    skip_upload_remote=skip_upload_remote,
                )
                stats[f'mapped_{hit_type}_urls' if hit_type in ('local', 'remote') else 'unresolved_urls'] += 1 if hit_type else 0

                general_txt_read, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                    text=str(general.get('txt_read') or ''),
                    source_json_relative=str(relative),
                    local_media_map=local_media_map,
                    local_variant_map=local_variant_map,
                    remote_url_cache=remote_url_cache,
                    uploader=uploader,
                    skip_upload_remote=skip_upload_remote,
                )
                stats['mapped_local_urls'] += s_local
                stats['mapped_remote_urls'] += s_remote
                stats['unresolved_urls'] += s_unresolved

                general_text_read_en, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                    text=str(general.get('text_read_en') or ''),
                    source_json_relative=str(relative),
                    local_media_map=local_media_map,
                    local_variant_map=local_variant_map,
                    remote_url_cache=remote_url_cache,
                    uploader=uploader,
                    skip_upload_remote=skip_upload_remote,
                )
                stats['mapped_local_urls'] += s_local
                stats['mapped_remote_urls'] += s_remote
                stats['unresolved_urls'] += s_unresolved

                general_text_read_vn, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                    text=str(general.get('text_read_vn') or ''),
                    source_json_relative=str(relative),
                    local_media_map=local_media_map,
                    local_variant_map=local_variant_map,
                    remote_url_cache=remote_url_cache,
                    uploader=uploader,
                    skip_upload_remote=skip_upload_remote,
                )
                stats['mapped_local_urls'] += s_local
                stats['mapped_remote_urls'] += s_remote
                stats['unresolved_urls'] += s_unresolved

                question_defaults = {
                    'display_order': order,
                    'kind': str(row.get('kind') or ''),
                    'title': str(row.get('title') or ''),
                    'jlpt_level': int(row.get('level') or 2),
                    'score': float(row.get('score') or 0),
                    'scores': row.get('scores') or [],
                    'correct_answers': row.get('correct_answers') or [],
                    'time_tracking': int(row.get('time_tracking') or 0),
                    'source_import': row.get('source_import') or {},
                    'raw_general': general,
                    'general_audio_url': mapped_general_audio,
                    'general_image_url': mapped_general_image,
                    'general_txt_read': general_txt_read,
                    'general_text_read_en': general_text_read_en,
                    'general_text_read_vn': general_text_read_vn,
                }

                question, q_created = N2Question.objects.update_or_create(
                    exam=exam,
                    source_id=source_id,
                    defaults=question_defaults,
                )
                if q_created:
                    stats['questions_created'] += 1
                else:
                    stats['questions_updated'] += 1

                content_rows = row.get('content') if isinstance(row.get('content'), list) else []
                for item_order, content in enumerate(content_rows):
                    if not isinstance(content, dict):
                        continue

                    mapped_item_image, hit_type = self._map_media_value(
                        value=str(content.get('image') or ''),
                        source_json_relative=str(relative),
                        local_media_map=local_media_map,
                        local_variant_map=local_variant_map,
                        remote_url_cache=remote_url_cache,
                        uploader=uploader,
                        skip_upload_remote=skip_upload_remote,
                    )
                    stats[f'mapped_{hit_type}_urls' if hit_type in ('local', 'remote') else 'unresolved_urls'] += 1 if hit_type else 0

                    question_text, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                        text=str(content.get('question') or ''),
                        source_json_relative=str(relative),
                        local_media_map=local_media_map,
                        local_variant_map=local_variant_map,
                        remote_url_cache=remote_url_cache,
                        uploader=uploader,
                        skip_upload_remote=skip_upload_remote,
                    )
                    stats['mapped_local_urls'] += s_local
                    stats['mapped_remote_urls'] += s_remote
                    stats['unresolved_urls'] += s_unresolved

                    explain = content.get('explainAll') if isinstance(content.get('explainAll'), dict) else {}
                    explain_en, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                        text=str(explain.get('en') or ''),
                        source_json_relative=str(relative),
                        local_media_map=local_media_map,
                        local_variant_map=local_variant_map,
                        remote_url_cache=remote_url_cache,
                        uploader=uploader,
                        skip_upload_remote=skip_upload_remote,
                    )
                    stats['mapped_local_urls'] += s_local
                    stats['mapped_remote_urls'] += s_remote
                    stats['unresolved_urls'] += s_unresolved

                    explain_vn, s_local, s_remote, s_unresolved = self._replace_media_urls_in_text(
                        text=str(explain.get('vn') or ''),
                        source_json_relative=str(relative),
                        local_media_map=local_media_map,
                        local_variant_map=local_variant_map,
                        remote_url_cache=remote_url_cache,
                        uploader=uploader,
                        skip_upload_remote=skip_upload_remote,
                    )
                    stats['mapped_local_urls'] += s_local
                    stats['mapped_remote_urls'] += s_remote
                    stats['unresolved_urls'] += s_unresolved

                    item_defaults = {
                        'question_text': question_text,
                        'image_url': mapped_item_image,
                        'answers': content.get('answers') or [],
                        'choose_answer': self._to_optional_int(content.get('chooseAnswer')),
                        'correct_answer': self._to_optional_int(content.get('correctAnswer')),
                        'explain_en': explain_en,
                        'explain_vn': explain_vn,
                        'raw_explain': explain,
                        'raw_data': content,
                    }

                    item, item_created = N2QuestionItem.objects.update_or_create(
                        question=question,
                        item_order=item_order,
                        defaults=item_defaults,
                    )
                    if item_created:
                        stats['items_created'] += 1
                    else:
                        stats['items_updated'] += 1

        return stats

    @staticmethod
    def _to_optional_int(value: Any) -> int | None:
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _section_sort_order(section_key: str) -> int:
        order = {'TuVung': 1, 'NguPhap': 2, 'Doc': 3, 'Nghe': 4}
        return order.get(section_key, 99)

    @staticmethod
    def _subcategory_sort_order(section_key: str, subcategory_key: str) -> int:
        section_order = {
            'TuVung': ['CachDocKanji', 'DongNghia', 'BieuHienTu', 'CachDungTu', 'CauTaoTu', 'CachDocHiragana'],
            'NguPhap': ['DangNguPhap', 'ThanhLapCau', 'NguPhapTheoDoanVan'],
            'Doc': ['DoanVanNgan', 'DoanVanTrungBinh', 'DocHieuChuDe', 'TimThongTin', 'DocHieuTongHop'],
            'Nghe': ['NgheHieuChuDe', 'NgheHieuDiemChinh', 'NgheHieuKhaiQuat', 'NgheHieuTongHop', 'TraLoiNhanh'],
        }
        candidates = section_order.get(section_key, [])
        if subcategory_key in candidates:
            return candidates.index(subcategory_key) + 1
        return 99

    def _map_media_value(
        self,
        *,
        value: str,
        source_json_relative: str,
        local_media_map: dict[str, UploadedMedia],
        local_variant_map: dict[str, set[str]],
        remote_url_cache: dict[str, str],
        uploader: R2Uploader,
        skip_upload_remote: bool,
    ) -> tuple[str, str]:
        """Return mapped value and hit type: local|remote|unresolved|''."""
        value = (value or '').strip()
        if not value:
            return '', ''

        if not value.startswith('http'):
            return value, ''

        mapped = self._map_url_to_local(value, source_json_relative, local_media_map, local_variant_map)
        if mapped:
            return mapped, 'local'

        if value in remote_url_cache:
            return remote_url_cache[value], 'remote'

        if skip_upload_remote:
            return value, 'unresolved'

        uploaded_url = self._download_and_upload_remote_url(value=value, uploader=uploader)
        if uploaded_url:
            remote_url_cache[value] = uploaded_url
            return uploaded_url, 'remote'

        return value, 'unresolved'

    def _map_url_to_local(
        self,
        url: str,
        source_json_relative: str,
        local_media_map: dict[str, UploadedMedia],
        local_variant_map: dict[str, set[str]],
    ) -> str:
        base = os.path.basename(urlparse(url).path)
        if not base:
            return ''

        if base in local_media_map and local_media_map[base].public_url:
            return local_media_map[base].public_url

        candidates = sorted(local_variant_map.get(base, set()))
        if not candidates:
            return ''

        if len(candidates) == 1:
            media = local_media_map.get(candidates[0])
            return media.public_url if media and media.public_url else ''

        # Context-based tie-breaker for highly generic basenames like Q1.mp3.
        context = source_json_relative.lower()
        narrowed = [c for c in candidates if self._candidate_matches_context(c, context)]
        target = narrowed[0] if len(narrowed) == 1 else ''
        if target:
            media = local_media_map.get(target)
            return media.public_url if media and media.public_url else ''

        return ''

    @staticmethod
    def _candidate_matches_context(candidate_basename: str, context: str) -> bool:
        # Keep conservative matching to avoid wrong audio assignment.
        # For ambiguous names (Q1.mp3 etc.), this intentionally returns False.
        lowered = candidate_basename.lower()
        tokens = ['nghehieuchude', 'nghehieudiemchinh', 'nghehieukhaiquat', 'nghehieutonghop', 'traloinhanh']
        if any(tok in context for tok in tokens):
            return any(tok in lowered for tok in tokens)
        return False

    def _replace_media_urls_in_text(
        self,
        *,
        text: str,
        source_json_relative: str,
        local_media_map: dict[str, UploadedMedia],
        local_variant_map: dict[str, set[str]],
        remote_url_cache: dict[str, str],
        uploader: R2Uploader,
        skip_upload_remote: bool,
    ) -> tuple[str, int, int, int]:
        text = text or ''
        if not text or 'http' not in text:
            return text, 0, 0, 0

        local_count = 0
        remote_count = 0
        unresolved_count = 0

        def repl(match: re.Match) -> str:
            nonlocal local_count, remote_count, unresolved_count
            raw_url = match.group(0)
            mapped, hit_type = self._map_media_value(
                value=raw_url,
                source_json_relative=source_json_relative,
                local_media_map=local_media_map,
                local_variant_map=local_variant_map,
                remote_url_cache=remote_url_cache,
                uploader=uploader,
                skip_upload_remote=skip_upload_remote,
            )
            if hit_type == 'local':
                local_count += 1
            elif hit_type == 'remote':
                remote_count += 1
            elif hit_type == 'unresolved':
                unresolved_count += 1
            return mapped or raw_url

        replaced = MEDIA_URL_RE.sub(repl, text)
        return replaced, local_count, remote_count, unresolved_count

    def _download_and_upload_remote_url(self, *, value: str, uploader: R2Uploader) -> str:
        try:
            resp = requests.get(value, timeout=20)
            if resp.status_code != 200:
                return ''
            data = resp.content
            if not data:
                return ''

            base = os.path.basename(urlparse(value).path)
            if not base:
                digest = hashlib.sha1(value.encode('utf-8')).hexdigest()[:12]
                base = f"remote_{digest}.bin"

            content_type = resp.headers.get('Content-Type', '').split(';')[0].strip()
            uploaded = uploader.upload_remote_bytes(
                source_url=value,
                data=data,
                basename=base,
                content_type=content_type,
            )

            media_type = self._detect_media_type(Path(base).suffix)
            self._upsert_media_asset(
                source_type=N2MediaAsset.SourceType.REMOTE,
                media_type=media_type,
                source_url=value,
                source_path='',
                source_basename=base,
                uploaded=uploaded,
                metadata={'fetched': True},
            )
            return uploaded.public_url
        except Exception:
            return ''
