"""
Cloudflare R2 (S3-compatible) helpers for direct avatar uploads.

Flow:
1) Backend creates a presigned PUT URL for a *specific* object key.
2) Client uploads bytes directly to R2 using that URL.
3) Client confirms the upload; backend verifies the object exists and stores the
   public URL on the user profile.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings


class R2StorageError(Exception):
    """Base exception for R2 storage errors."""


class R2StorageConfigError(R2StorageError):
    """Raised when required R2 settings are missing."""


class R2ObjectNotFoundError(R2StorageError):
    """Raised when a referenced object key does not exist."""


class R2StorageBadRequestError(R2StorageError):
    """Raised when client input is invalid (e.g., malformed key)."""


class R2StorageAPIError(R2StorageError):
    """Raised when the S3-compatible API returns an error."""


_S3_CLIENT = None


def is_configured() -> bool:
    return bool(
        settings.R2_ENDPOINT_URL
        and settings.R2_BUCKET_NAME
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
        and settings.R2_PUBLIC_BASE_URL
    )


def _ensure_config():
    missing: list[str] = []
    if not settings.R2_ENDPOINT_URL:
        missing.append('R2_ENDPOINT_URL')
    if not settings.R2_BUCKET_NAME:
        missing.append('R2_BUCKET_NAME')
    if not settings.R2_ACCESS_KEY_ID:
        missing.append('R2_ACCESS_KEY_ID')
    if not settings.R2_SECRET_ACCESS_KEY:
        missing.append('R2_SECRET_ACCESS_KEY')
    if not settings.R2_PUBLIC_BASE_URL:
        missing.append('R2_PUBLIC_BASE_URL')
    if missing:
        raise R2StorageConfigError(f"Missing R2 settings: {', '.join(missing)}")


def _avatar_prefix() -> str:
    prefix = (getattr(settings, 'R2_AVATAR_PREFIX', '') or 'avatar/').strip()
    if not prefix.endswith('/'):
        prefix += '/'
    # Disallow absolute paths.
    prefix = prefix.lstrip('/')
    return prefix


def _s3_client():
    global _S3_CLIENT
    if _S3_CLIENT is not None:
        return _S3_CLIENT

    _ensure_config()

    # R2 requires path-style addressing for the account-level endpoint URL.
    cfg = Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'},
    )
    _S3_CLIENT = boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        region_name=getattr(settings, 'R2_REGION', 'auto') or 'auto',
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=cfg,
    )
    return _S3_CLIENT


def looks_like_avatar_key(key: str) -> bool:
    prefix = _avatar_prefix()
    return bool(key and isinstance(key, str) and key.startswith(prefix))


def _validate_avatar_key_for_user(key: str, user_id: str):
    prefix = _avatar_prefix()
    if not key or not isinstance(key, str):
        raise R2StorageBadRequestError('Invalid avatar key.')
    if key.startswith('/'):
        raise R2StorageBadRequestError('Invalid avatar key.')
    if '\\' in key or '..' in key:
        raise R2StorageBadRequestError('Invalid avatar key.')
    if not key.startswith(prefix):
        raise R2StorageBadRequestError('Avatar key does not match expected prefix.')
    expected = f"{prefix}{str(user_id).strip()}/"
    if not key.startswith(expected):
        raise R2StorageBadRequestError('Avatar key does not belong to current user.')


def public_url(key: str) -> str:
    base = (settings.R2_PUBLIC_BASE_URL or '').rstrip('/')
    return f"{base}/{key.lstrip('/')}"


def create_avatar_upload(*, user_id: str, content_type: str | None = None, filename: str | None = None) -> dict[str, Any]:
    """
    Create a presigned PUT URL for direct avatar uploads.

    Returns a payload compatible with the existing avatar upload flow:
      {
        "image_id": "<object key>",
        "upload_url": "<presigned url>",
        "method": "PUT",
        "headers": {"Content-Type": "..."},
        "public_url": "...",
        "expires_in": 600,
        "max_bytes": 5242880
      }
    """
    _ensure_config()
    s3 = _s3_client()

    user_id = str(user_id).strip()
    if not user_id:
        raise R2StorageBadRequestError('user_id is required.')

    # Keep the key short to fit in the existing `avatar_image_id` DB field.
    ext = ''
    if filename:
        _, raw_ext = os.path.splitext(str(filename))
        raw_ext = raw_ext.lower()
        if raw_ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
            ext = raw_ext

    key = f"{_avatar_prefix()}{user_id}/{uuid.uuid4().hex}{ext}"
    expires = int(getattr(settings, 'R2_PRESIGNED_EXPIRES', 600) or 600)
    max_bytes = int(getattr(settings, 'R2_MAX_UPLOAD_BYTES', 0) or 0)

    try:
        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': settings.R2_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires,
            HttpMethod='PUT',
        )
    except (BotoCoreError, ClientError) as exc:
        raise R2StorageAPIError(f'Failed to create presigned upload URL: {exc}') from exc

    headers: dict[str, str] = {}
    if content_type:
        headers['Content-Type'] = str(content_type)

    return {
        'image_id': key,
        'upload_url': upload_url,
        'method': 'PUT',
        'headers': headers,
        'public_url': public_url(key),
        'expires_in': expires,
        'max_bytes': max_bytes,
    }


_ALLOWED_IMAGE_CONTENT_TYPES: dict[str, str] = {
    # content-type -> default extension (used when filename has no valid extension)
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/webp': '.webp',
    'image/gif': '.gif',
}

_EXT_TO_CONTENT_TYPE: dict[str, str] = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
}


def upload_avatar_file(
    *,
    user_id: str,
    fileobj,
    content_type: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    """
    Upload an avatar to R2 via backend (server-side upload).

    This is an alternative to presigned URLs for non-browser clients that prefer
    a single backend API call.
    """
    _ensure_config()
    s3 = _s3_client()

    user_id = str(user_id).strip()
    if not user_id:
        raise R2StorageBadRequestError('user_id is required.')

    ext = ''
    if filename:
        _, raw_ext = os.path.splitext(str(filename))
        raw_ext = raw_ext.lower()
        if raw_ext in _EXT_TO_CONTENT_TYPE:
            ext = raw_ext

    ct = (str(content_type).strip().lower() if content_type else '') or None
    if ct in ('application/octet-stream', 'binary/octet-stream'):
        ct = None
    if ct and ct not in _ALLOWED_IMAGE_CONTENT_TYPES:
        raise R2StorageBadRequestError('Unsupported image content type.')
    if not ext and ct:
        ext = _ALLOWED_IMAGE_CONTENT_TYPES.get(ct, '')
    if not ct and ext:
        ct = _EXT_TO_CONTENT_TYPE.get(ext)
    if not ct:
        raise R2StorageBadRequestError('content_type or filename is required.')

    key = f"{_avatar_prefix()}{user_id}/{uuid.uuid4().hex}{ext}"

    put_kwargs: dict[str, Any] = {
        'Bucket': settings.R2_BUCKET_NAME,
        'Key': key,
        'Body': fileobj,
        # New key per upload -> immutable caching is safe and prevents needless re-fetches.
        'CacheControl': 'public, max-age=31536000, immutable',
    }
    if ct:
        put_kwargs['ContentType'] = ct

    try:
        s3.put_object(**put_kwargs)
    except (BotoCoreError, ClientError) as exc:
        raise R2StorageAPIError(f'Failed to upload avatar object: {exc}') from exc

    return {
        'image_id': key,
        'public_url': public_url(key),
    }


def head_avatar(*, key: str, user_id: str) -> dict[str, Any]:
    _ensure_config()
    _validate_avatar_key_for_user(key, user_id=user_id)
    s3 = _s3_client()
    try:
        return s3.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except ClientError as exc:
        code = str((exc.response or {}).get('Error', {}).get('Code') or '')
        if code in ('404', 'NoSuchKey', 'NotFound'):
            raise R2ObjectNotFoundError('Avatar upload is not completed yet.') from exc
        raise R2StorageAPIError(f'Failed to verify uploaded object: {exc}') from exc
    except BotoCoreError as exc:
        raise R2StorageAPIError(f'Failed to verify uploaded object: {exc}') from exc


def delete_avatar(*, key: str, user_id: str | None = None):
    _ensure_config()
    if user_id is not None:
        _validate_avatar_key_for_user(key, user_id=user_id)
    s3 = _s3_client()
    try:
        s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise R2StorageAPIError(f'Failed to delete avatar object: {exc}') from exc
