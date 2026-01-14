"""
Payment provider registry and factory.
Central point for accessing payment providers.
"""
import logging
from typing import Optional, Dict, Type
from django.conf import settings

from apps.transactions.services.payment_provider import PaymentProvider

logger = logging.getLogger(__name__)

# Registry of available providers
_providers: Dict[str, Type[PaymentProvider]] = {}
_instances: Dict[str, PaymentProvider] = {}


def register_provider(name: str, provider_class: Type[PaymentProvider]):
    """Register a payment provider."""
    _providers[name] = provider_class
    logger.info(f"Registered payment provider: {name}")


def get_provider(name: str) -> Optional[PaymentProvider]:
    """
    Get a payment provider instance by name.
    Instances are cached for reuse.
    """
    if name in _instances:
        return _instances[name]
    
    if name not in _providers:
        logger.error(f"Payment provider not found: {name}")
        return None
    
    try:
        instance = _providers[name]()
        _instances[name] = instance
        return instance
    except Exception as e:
        logger.exception(f"Failed to instantiate provider {name}: {e}")
        return None


def get_default_provider() -> Optional[PaymentProvider]:
    """Get the default payment provider from settings."""
    default_name = getattr(settings, 'DEFAULT_PAYMENT_PROVIDER', 'mpesa')
    return get_provider(default_name)


def get_provider_for_currency(currency: str) -> Optional[PaymentProvider]:
    """Get a provider that supports the given currency."""
    for name, provider_class in _providers.items():
        provider = get_provider(name)
        if provider and currency in provider.supported_currencies:
            return provider
    return None


def list_providers() -> list:
    """List all registered provider names."""
    return list(_providers.keys())


# Auto-register providers on module import
def _auto_register():
    """Auto-register available providers."""
    try:
        from apps.transactions.services.mpesa_provider import MpesaProvider
        register_provider('mpesa', MpesaProvider)
    except ImportError:
        logger.warning("M-Pesa provider not available")

    # Future providers
    # try:
    #     from apps.transactions.services.stripe_provider import StripeProvider
    #     register_provider('stripe', StripeProvider)
    # except ImportError:
    #     pass


_auto_register()
