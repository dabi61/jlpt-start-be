"""
Helpers for standard API response envelope.
"""
from http import HTTPStatus

from rest_framework.exceptions import ErrorDetail


def response_type(code):
    """Return SUCCESS for <400 and ERROR for >=400."""
    return 'ERROR' if int(code) >= 400 else 'SUCCESS'


def default_message(code):
    """Return default message for status code."""
    code = int(code)
    fallback_map = {
        200: 'Request successful.',
        201: 'Resource created successfully.',
        202: 'Request accepted.',
        204: 'Request successful.',
        400: 'Invalid request.',
        401: 'Missing or invalid authorization header.',
        403: 'You do not have permission to perform this action.',
        404: 'Resource not found.',
        405: 'Method not allowed.',
        409: 'Request conflicts with current state.',
        429: 'Too many requests.',
        500: 'Internal server error.',
    }
    if code in fallback_map:
        return fallback_map[code]

    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return 'Request failed.' if code >= 400 else 'Request successful.'


def extract_message(payload):
    """Extract first human-readable message from payload."""
    if payload is None:
        return ''

    if isinstance(payload, ErrorDetail):
        return str(payload)

    if isinstance(payload, str):
        return payload

    if isinstance(payload, list):
        for item in payload:
            message = extract_message(item)
            if message:
                return message
        return ''

    if isinstance(payload, dict):
        # Already enveloped payload.
        meta = payload.get('meta')
        if isinstance(meta, dict):
            message = meta.get('message')
            if message:
                return str(message)

        for key in ('message', 'detail', 'error'):
            if key in payload:
                message = extract_message(payload.get(key))
                if message:
                    return message

        for value in payload.values():
            message = extract_message(value)
            if message:
                return message
        return ''

    return str(payload)


def extract_success_message(payload):
    """
    Extract message for successful responses without guessing from business fields.
    """
    if payload is None:
        return ''

    if isinstance(payload, ErrorDetail):
        return str(payload)

    if isinstance(payload, str):
        return payload

    if isinstance(payload, dict):
        if 'message' in payload:
            return extract_message(payload.get('message'))

        # Typical 3rd-party success payload like {"detail": "..."}.
        if len(payload) == 1 and 'detail' in payload:
            return extract_message(payload.get('detail'))

    return ''


def normalize_success_data(payload):
    """
    Keep business payload in `data` for successful responses.
    Remove top-level message field because it is moved to meta.message.
    """
    if payload is None:
        return {}

    if isinstance(payload, dict):
        normalized = dict(payload)
        normalized.pop('message', None)

        # Common success payload from 3rd-party auth endpoints.
        if (
            len(normalized) == 1
            and isinstance(normalized.get('detail'), str)
        ):
            return {}

        return normalized

    return payload


def build_envelope(code, message=None, data=None):
    """Build canonical API response envelope."""
    resolved_code = int(code)
    resolved_message = message or default_message(resolved_code)

    if data is None:
        data = {}

    return {
        'meta': {
            'code': resolved_code,
            'type': response_type(resolved_code),
            'message': resolved_message,
        },
        'data': data,
    }
