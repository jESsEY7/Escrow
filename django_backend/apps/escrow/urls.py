"""
Escrow URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from apps.escrow.views import EscrowViewSet, MilestoneViewSet

app_name = 'escrow'

# Main router
router = DefaultRouter()
router.register(r'', EscrowViewSet, basename='escrow')

# Nested router for milestones
escrow_router = nested_routers.NestedDefaultRouter(router, r'', lookup='escrow')
escrow_router.register(r'milestones', MilestoneViewSet, basename='escrow-milestones')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(escrow_router.urls)),
]
