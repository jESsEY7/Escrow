"""
Development settings for Escrow Platform.
"""

import os
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - SQLite for development (can switch to PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If DATABASE_URL is set, use PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(DATABASE_URL)
    except ImportError:
        pass

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Email - Console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar (optional)
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS = ['debug_toolbar'] + INSTALLED_APPS
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Logging - More verbose in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Disable rate limiting in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/hour',
    'user': '100000/hour',
    'login': '100/minute',
}

# Payment providers - Sandbox/Test mode
PAYMENT_PROVIDERS = {
    'stripe': {
        'secret_key': os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...'),
        'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...'),
        'webhook_secret': os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
        'test_mode': True,
    },
    'mpesa': {
        'consumer_key': os.environ.get('MPESA_CONSUMER_KEY', ''),
        'consumer_secret': os.environ.get('MPESA_CONSUMER_SECRET', ''),
        'passkey': os.environ.get('MPESA_PASSKEY', ''),
        'shortcode': os.environ.get('MPESA_SHORTCODE', ''),
        'callback_url': os.environ.get('MPESA_CALLBACK_URL', 'http://localhost:8000/api/payments/mpesa/callback/'),
        'test_mode': True,
    },
}

print("🚀 Running in DEVELOPMENT mode")
