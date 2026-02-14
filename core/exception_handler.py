"""
Custom DRF exception handler for consistent API error format.
"""
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .response_envelope import default_message, extract_message


def _integrity_error_message(exc):
    """Map low-level DB integrity errors to client-safe messages."""
    raw_message = str(exc).lower()

    if 'duplicate key value' in raw_message or 'unique constraint' in raw_message:
        return 'Duplicate value violates a unique constraint.'

    if 'null value in column' in raw_message:
        return 'A required field is missing.'

    if 'foreign key constraint' in raw_message:
        return 'Referenced resource does not exist.'

    return 'Database integrity constraint violated.'


def custom_exception_handler(exc, context):
    """
    Return consistent error payloads.
    All API errors return: {"message": "..."}.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        if isinstance(exc, IntegrityError):
            message = _integrity_error_message(exc)
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'message': default_message(status.HTTP_500_INTERNAL_SERVER_ERROR)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = extract_message(response.data)

    if not message:
        message = default_message(response.status_code)

    response.data = {'message': message}

    return response
