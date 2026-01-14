"""
Custom exception handler for the Escrow Platform.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception
    if response is None:
        if isinstance(exc, DjangoValidationError):
            return Response(
                {
                    'error': 'Validation Error',
                    'message': str(exc),
                    'code': 'validation_error',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log unhandled exceptions
        logger.exception(f'Unhandled exception: {exc}')
        
        return Response(
            {
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Please try again later.',
                'code': 'internal_error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Standardize error response format
    if response is not None:
        error_response = {
            'error': get_error_title(response.status_code),
            'code': getattr(exc, 'default_code', 'error'),
        }

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_response['message'] = response.data['detail']
            elif 'message' in response.data:
                error_response['message'] = response.data['message']
            else:
                error_response['details'] = response.data
        elif isinstance(response.data, list):
            error_response['errors'] = response.data
        else:
            error_response['message'] = str(response.data)

        response.data = error_response

    return response


def get_error_title(status_code):
    """Get human-readable error title for status code."""
    titles = {
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        409: 'Conflict',
        422: 'Unprocessable Entity',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
    }
    return titles.get(status_code, 'Error')
