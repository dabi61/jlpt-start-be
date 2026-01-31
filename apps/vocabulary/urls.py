"""
URL patterns for Vocabulary app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WordViewSet

app_name = 'vocabulary'

router = DefaultRouter()
router.register('', WordViewSet, basename='word')

urlpatterns = [
    path('', include(router.urls)),
]
