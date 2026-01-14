"""
Audit middleware for the Escrow Platform.
"""
from apps.audit.services.audit_service import AuditService


class AuditMiddleware:
    """Set audit context for all requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set request context for audit logging
        AuditService.set_request_context(request)

        try:
            response = self.get_response(request)
            return response
        finally:
            # Clear context after request
            AuditService.clear_request_context()
