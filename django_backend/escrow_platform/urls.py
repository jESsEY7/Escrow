"""
URL configuration for Escrow Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'version': '1.0.0',
        'environment': 'development' if settings.DEBUG else 'production',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint."""
    return Response({
        'message': 'Escrow Platform API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'users': '/api/users/',
            'escrow': '/api/escrow/',
            'transactions': '/api/transactions/',
            'disputes': '/api/disputes/',
            'admin': '/api/admin/',
        },
        'docs': '/api/docs/',
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # API root
    path('api/', api_root, name='api_root'),
    
    # API endpoints
    path('api/auth/', include('apps.users.urls.auth_urls', namespace='auth')),
    path('api/users/', include('apps.users.urls.user_urls', namespace='users')),
    path('api/escrow/', include('apps.escrow.urls', namespace='escrow')),
    path('api/transactions/', include('apps.transactions.urls', namespace='transactions')),
    path('api/disputes/', include('apps.disputes.urls', namespace='disputes')),
    path('api/admin/', include('apps.audit.urls', namespace='audit')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.core.urls', namespace='core')),
]

# Debug toolbar in development
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
