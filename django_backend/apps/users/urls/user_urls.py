"""
User profile URLs for the Escrow Platform.
"""
from django.urls import path
from apps.users.views import (
    MeView,
    PasswordChangeView,
    KYCSubmitView,
    KYCStatusView,
)

app_name = 'users'

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('kyc/submit/', KYCSubmitView.as_view(), name='kyc_submit'),
    path('kyc/status/', KYCStatusView.as_view(), name='kyc_status'),
]
