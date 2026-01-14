"""
Security middleware for the Escrow Platform.
"""
import uuid
import time
import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )

        return response


class RequestLoggingMiddleware:
    """Log all incoming requests with timing information."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate request ID
        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        request.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get response
        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Add request ID to response
        response['X-Request-ID'] = request_id

        # Log request (skip static files and health checks)
        if not request.path.startswith(('/static/', '/media/', '/health')):
            self._log_request(request, response, duration)

        return response

    def _log_request(self, request, response, duration):
        """Log request details."""
        log_data = {
            'request_id': getattr(request, 'request_id', '-'),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user': str(request.user.id) if request.user.is_authenticated else 'anonymous',
            'ip': self._get_client_ip(request),
        }

        if response.status_code >= 500:
            logger.error('Request failed', extra=log_data)
        elif response.status_code >= 400:
            logger.warning('Request error', extra=log_data)
        else:
            logger.info('Request completed', extra=log_data)

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RateLimitMiddleware:
    """
    Additional rate limiting for sensitive endpoints.
    Works alongside DRF throttling.
    """

    SENSITIVE_ENDPOINTS = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/auth/password/reset/',
        '/api/escrow/',  # Creating escrows
        '/api/transactions/',  # Payment operations
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self._rate_limit_cache = {}

    def __call__(self, request):
        # Check if endpoint is sensitive
        if self._is_sensitive_endpoint(request.path):
            if self._is_rate_limited(request):
                return JsonResponse(
                    {'error': 'Too many requests. Please try again later.'},
                    status=429
                )

        return self.get_response(request)

    def _is_sensitive_endpoint(self, path):
        """Check if path matches sensitive endpoints."""
        return any(path.startswith(endpoint) for endpoint in self.SENSITIVE_ENDPOINTS)

    def _is_rate_limited(self, request):
        """Check if request should be rate limited."""
        # Simple in-memory rate limiting
        # In production, use Redis-based rate limiting
        ip = self._get_client_ip(request)
        current_time = time.time()
        window = 60  # 1 minute window
        max_requests = 30

        key = f"{ip}:{request.path}"
        
        if key not in self._rate_limit_cache:
            self._rate_limit_cache[key] = []

        # Clean old entries
        self._rate_limit_cache[key] = [
            t for t in self._rate_limit_cache[key]
            if current_time - t < window
        ]

        # Check limit
        if len(self._rate_limit_cache[key]) >= max_requests:
            return True

        # Record request
        self._rate_limit_cache[key].append(current_time)
        return False

    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class InputSanitizationMiddleware:
    """Sanitize input to prevent injection attacks."""

    DANGEROUS_PATTERNS = [
        '<script',
        'javascript:',
        'data:text/html',
        'onclick=',
        'onerror=',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check query parameters
        for key, value in request.GET.items():
            if self._contains_dangerous_content(value):
                return JsonResponse(
                    {'error': 'Invalid input detected'},
                    status=400
                )

        # Check POST data
        if request.content_type == 'application/x-www-form-urlencoded':
            for key, value in request.POST.items():
                if self._contains_dangerous_content(value):
                    return JsonResponse(
                        {'error': 'Invalid input detected'},
                        status=400
                    )

        return self.get_response(request)

    def _contains_dangerous_content(self, value):
        """Check if value contains dangerous patterns."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in self.DANGEROUS_PATTERNS)
