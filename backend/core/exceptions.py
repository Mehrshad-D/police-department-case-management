"""
Centralized exception handling for REST API.
Returns consistent error payloads and appropriate status codes.
"""
import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF; returns uniform error format."""
    response = exception_handler(exc, context)
    if response is not None:
        payload = {
            'success': False,
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': str(exc) if str(exc) else 'Request failed',
                'details': response.data,
            },
        }
        response.data = payload
        return response

    # Unhandled exception (e.g. 500)
    logger.exception("Unhandled exception in API: %s", exc)
    return Response(
        {
            'success': False,
            'error': {
                'code': 'server_error',
                'message': 'An unexpected error occurred.',
                'details': None,
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
