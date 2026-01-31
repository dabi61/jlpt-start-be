"""
URL patterns for Kanji app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import KanjiViewSet

app_name = 'kanjis'

router = DefaultRouter()
router.register('', KanjiViewSet, basename='kanji')

urlpatterns = router.urls
