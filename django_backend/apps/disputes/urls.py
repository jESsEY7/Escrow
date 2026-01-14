"""
Dispute URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.disputes.views import DisputeViewSet

app_name = 'disputes'

router = DefaultRouter()
router.register(r'', DisputeViewSet, basename='dispute')

urlpatterns = [
    path('', include(router.urls)),
]
