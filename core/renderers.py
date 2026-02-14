"""
Custom DRF renderer to wrap responses in the global API envelope.
"""
from rest_framework.renderers import JSONRenderer

from .response_envelope import (
    build_envelope,
    default_message,
    extract_message,
    extract_success_message,
    normalize_success_data,
    response_type,
)


class EnvelopedJSONRenderer(JSONRenderer):
    """
    Wrap every DRF JSON response into:
    {
      "meta": {"code": ..., "type": "SUCCESS|ERROR", "message": "..."},
      "data": ...
    }
    """

    # Keep schema endpoint raw so OpenAPI clients and Swagger can parse it.
    bypass_path_prefixes = ('/api/schema/',)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        request = renderer_context.get('request')
        response = renderer_context.get('response')

        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        request_path = getattr(request, 'path', '') if request else ''
        if any(request_path.startswith(prefix) for prefix in self.bypass_path_prefixes):
            return super().render(data, accepted_media_type, renderer_context)

        # If a view already returns the envelope, only backfill missing meta fields.
        if isinstance(data, dict) and 'meta' in data and 'data' in data:
            meta = data.get('meta') if isinstance(data.get('meta'), dict) else {}
            status_code = int(meta.get('code') or response.status_code or 200)
            meta.setdefault('code', status_code)
            meta.setdefault('type', response_type(status_code))
            meta.setdefault('message', default_message(status_code))
            data['meta'] = meta
            data.setdefault('data', {})
            return super().render(data, accepted_media_type, renderer_context)

        status_code = int(response.status_code or 200)
        if status_code >= 400:
            message = extract_message(data) or default_message(status_code)
            payload_data = {}
        else:
            message = extract_success_message(data) or default_message(status_code)
            payload_data = normalize_success_data(data)

        envelope = build_envelope(
            code=status_code,
            message=message,
            data=payload_data,
        )
        return super().render(envelope, accepted_media_type, renderer_context)
