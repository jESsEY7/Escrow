"""
Rate limiting middleware for the Escrow Platform.
Protects API endpoints from abuse and DDoS attacks.
"""
import time
import hashlib
import logging
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware using sliding window algorithm.
    
    Configuration in settings.py:
        RATE_LIMIT_CONFIG = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'auth': {'requests': 5, 'window': 60},        # 5 req/min for auth
            'payment': {'requests': 10, 'window': 60},    # 10 req/min for payments
        }
    """
    
    # Endpoint patterns to rate limit categories
    ENDPOINT_CATEGORIES = {
        '/api/auth/': 'auth',
        '/api/users/login': 'auth',
        '/api/users/register': 'auth',
        '/api/users/password': 'auth',
        '/api/transactions/': 'payment',
        '/api/escrow/': 'payment',
    }
    
    # Endpoints to exclude from rate limiting
    EXCLUDED_PATHS = [
        '/api/health/',
        '/api/transactions/mpesa/callback/',  # Webhooks need to pass through
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'RATE_LIMIT_CONFIG', {
            'default': {'requests': 100, 'window': 60},
            'auth': {'requests': 5, 'window': 60},
            'payment': {'requests': 20, 'window': 60},
        })

    def __call__(self, request):
        # Skip excluded paths
        if self._is_excluded(request.path):
            return self.get_response(request)
        
        # Get rate limit key and config
        client_key = self._get_client_key(request)
        category = self._get_category(request.path)
        limit_config = self.config.get(category, self.config['default'])
        
        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(
            client_key,
            limit_config['requests'],
            limit_config['window']
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_key} on {request.path}")
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please retry after {retry_after} seconds.',
                    'retry_after': retry_after,
                },
                status=429,
                headers={'Retry-After': str(retry_after)}
            )
        
        response = self.get_response(request)
        
        # Add rate limit headers
        remaining, reset_time = self._get_remaining(
            client_key,
            limit_config['requests'],
            limit_config['window']
        )
        response['X-RateLimit-Limit'] = str(limit_config['requests'])
        response['X-RateLimit-Remaining'] = str(max(0, remaining))
        response['X-RateLimit-Reset'] = str(int(reset_time))
        
        return response

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)

    def _get_category(self, path: str) -> str:
        """Get rate limit category for path."""
        for pattern, category in self.ENDPOINT_CATEGORIES.items():
            if path.startswith(pattern):
                return category
        return 'default'

    def _get_client_key(self, request) -> str:
        """Generate unique key for client identification."""
        # Use user ID if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
        else:
            user_id = 'anon'
        
        # Get IP address
        ip = self._get_client_ip(request)
        
        # Combine for key
        raw_key = f"ratelimit:{user_id}:{ip}:{self._get_category(request.path)}"
        return hashlib.md5(raw_key.encode()).hexdigest()

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def _check_rate_limit(self, key: str, max_requests: int, window: int) -> tuple:
        """
        Check if request is within rate limit using sliding window.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        window_key = f"{key}:window"
        
        # Get current window data
        window_data = cache.get(window_key, {'requests': [], 'start': now})
        
        # Remove expired requests from window
        cutoff = now - window
        window_data['requests'] = [
            ts for ts in window_data['requests'] if ts > cutoff
        ]
        
        # Check if under limit
        if len(window_data['requests']) >= max_requests:
            # Calculate retry time
            oldest = min(window_data['requests']) if window_data['requests'] else now
            retry_after = int(oldest + window - now) + 1
            return False, max(1, retry_after)
        
        # Add current request
        window_data['requests'].append(now)
        cache.set(window_key, window_data, timeout=window * 2)
        
        return True, 0

    def _get_remaining(self, key: str, max_requests: int, window: int) -> tuple:
        """Get remaining requests and reset time."""
        now = time.time()
        window_key = f"{key}:window"
        
        window_data = cache.get(window_key, {'requests': [], 'start': now})
        
        # Count valid requests
        cutoff = now - window
        valid_requests = [ts for ts in window_data['requests'] if ts > cutoff]
        
        remaining = max_requests - len(valid_requests)
        reset_time = (min(valid_requests) + window) if valid_requests else (now + window)
        
        return remaining, reset_time


class IPBlockMiddleware:
    """
    Middleware to block known malicious IPs.
    Checks against a cached blocklist.
    """
    
    BLOCKLIST_CACHE_KEY = 'ip_blocklist'
    BLOCKLIST_TTL = 300  # 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_client_ip(request)
        
        if self._is_blocked(ip):
            logger.warning(f"Blocked request from IP: {ip}")
            return JsonResponse(
                {'error': 'Access denied'},
                status=403
            )
        
        return self.get_response(request)

    def _get_client_ip(self, request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _is_blocked(self, ip: str) -> bool:
        """Check if IP is in blocklist."""
        blocklist = cache.get(self.BLOCKLIST_CACHE_KEY, set())
        return ip in blocklist

    @classmethod
    def block_ip(cls, ip: str, duration: int = 3600):
        """Add IP to blocklist."""
        blocklist = cache.get(cls.BLOCKLIST_CACHE_KEY, set())
        blocklist.add(ip)
        cache.set(cls.BLOCKLIST_CACHE_KEY, blocklist, timeout=duration)
        logger.info(f"Blocked IP {ip} for {duration} seconds")

    @classmethod
    def unblock_ip(cls, ip: str):
        """Remove IP from blocklist."""
        blocklist = cache.get(cls.BLOCKLIST_CACHE_KEY, set())
        blocklist.discard(ip)
        cache.set(cls.BLOCKLIST_CACHE_KEY, blocklist)
        logger.info(f"Unblocked IP {ip}")
