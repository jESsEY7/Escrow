from django.urls import path
from .views import ContactView

app_name = 'core'

urlpatterns = [
    path('contact/', ContactView.as_view(), name='contact'),
]
