"""
Cloudflare Images integration helpers.
"""
from typing import Any
import json

import requests
from django.conf import settings


class CloudflareImagesError(Exception):
    """Base exception for Cloudflare Images errors."""


class CloudflareImagesConfigError(CloudflareImagesError):
    """Raised when required Cloudflare settings are missing."""


class CloudflareImagesAPIError(CloudflareImagesError):
    """Raised when Cloudflare API returns an error."""


def is_configured() -> bool:
    return bool(settings.CF_ACCOUNT_ID and settings.CF_IMAGES_API_TOKEN)


def _ensure_config():
    if not settings.CF_ACCOUNT_ID:
        raise CloudflareImagesConfigError('Cloudflare account id is not configured.')
    if not settings.CF_IMAGES_API_TOKEN:
        raise CloudflareImagesConfigError('Cloudflare Images API token is not configured.')


def _api_url(path: str) -> str:
    _ensure_config()
    return f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}{path}"


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    as_form: bool = False,
) -> dict[str, Any]:
    url = _api_url(path)
    headers = {
        'Authorization': f"Bearer {settings.CF_IMAGES_API_TOKEN}",
    }
    kwargs = {
        'headers': headers,
        'timeout': settings.CF_IMAGES_TIMEOUT,
    }
    if payload is not None:
        if as_form:
            kwargs['data'] = payload
        else:
            kwargs['json'] = payload

    try:
        response = requests.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise CloudflareImagesAPIError(f'Cloudflare request failed: {exc}') from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise CloudflareImagesAPIError('Cloudflare response is not valid JSON.') from exc

    if response.status_code >= 400 or not body.get('success', False):
        errors = body.get('errors') or []
        message = ''
        if errors and isinstance(errors[0], dict):
            message = str(errors[0].get('message') or '')
        if not message:
            message = f'Cloudflare Images API error (status {response.status_code}).'
        raise CloudflareImagesAPIError(message)

    result = body.get('result')
    if result is None:
        raise CloudflareImagesAPIError('Cloudflare response missing result payload.')
    return result


def create_direct_upload(user_id: str) -> dict[str, str]:
    """
    Create a one-time direct upload URL for client-side upload.
    """
    url = _api_url('/images/v2/direct_upload')
    headers = {
        'Authorization': f"Bearer {settings.CF_IMAGES_API_TOKEN}",
    }
    files = {
        'requireSignedURLs': (None, 'false'),
        'metadata': (None, json.dumps({'user_id': str(user_id)})),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            files=files,
            timeout=settings.CF_IMAGES_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise CloudflareImagesAPIError(f'Cloudflare request failed: {exc}') from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise CloudflareImagesAPIError('Cloudflare response is not valid JSON.') from exc

    if response.status_code >= 400 or not body.get('success', False):
        errors = body.get('errors') or []
        message = ''
        if errors and isinstance(errors[0], dict):
            message = str(errors[0].get('message') or '')
        if not message:
            message = f'Cloudflare Images API error (status {response.status_code}).'
        raise CloudflareImagesAPIError(message)

    result = body.get('result')
    if result is None:
        raise CloudflareImagesAPIError('Cloudflare response missing result payload.')

    image_id = result.get('id')
    upload_url = result.get('uploadURL')
    if not image_id or not upload_url:
        raise CloudflareImagesAPIError('Cloudflare direct upload response is missing id or uploadURL.')

    return {
        'image_id': image_id,
        'upload_url': upload_url,
    }


def get_image(image_id: str) -> dict[str, Any]:
    return _request('GET', f'/images/v1/{image_id}')


def delete_image(image_id: str):
    _request('DELETE', f'/images/v1/{image_id}')


def resolve_avatar_url(image: dict[str, Any]) -> str:
    """
    Resolve avatar URL from image variants. Falls back to account hash if configured.
    """
    image_id = str(image.get('id') or '').strip()
    variant_name = settings.CF_IMAGES_AVATAR_VARIANT
    variants = image.get('variants') or []

    for url in variants:
        if isinstance(url, str) and url.rstrip('/').endswith(f'/{variant_name}'):
            return url

    if variants and isinstance(variants[0], str):
        return variants[0]

    if settings.CF_IMAGES_ACCOUNT_HASH and image_id:
        return f"https://imagedelivery.net/{settings.CF_IMAGES_ACCOUNT_HASH}/{image_id}/{variant_name}"

    raise CloudflareImagesConfigError(
        'Cannot resolve avatar URL. Create a Cloudflare variant or configure CF_IMAGES_ACCOUNT_HASH.'
    )
