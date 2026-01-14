"""
Transaction URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.transactions.views import TransactionViewSet, UserTransactionsView
from apps.transactions.views.mpesa_views import (
    initiate_mpesa_payment,
    mpesa_callback,
    check_payment_status,
    query_mpesa_status,
)

app_name = 'transactions'

router = DefaultRouter()
router.register(r'', TransactionViewSet, basename='transaction')

urlpatterns = [
    # M-Pesa endpoints
    path('mpesa/initiate/', initiate_mpesa_payment, name='mpesa_initiate'),
    path('mpesa/callback/', mpesa_callback, name='mpesa_callback'),
    path('mpesa/status/<str:checkout_request_id>/', check_payment_status, name='mpesa_status'),
    path('mpesa/query/', query_mpesa_status, name='mpesa_query'),
    
    # Other endpoints
    path('my/', UserTransactionsView.as_view(), name='my_transactions'),
    path('', include(router.urls)),
]
