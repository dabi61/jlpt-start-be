"""
URL patterns for Grammar app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GrammarViewSet

app_name = 'grammar'

router = DefaultRouter()
router.register('', GrammarViewSet, basename='grammar')

urlpatterns = router.urls
