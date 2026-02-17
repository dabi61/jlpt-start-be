"""URL patterns for Practice (attempt/answer) APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PracticeAttemptViewSet

app_name = 'practice'

router = DefaultRouter()
router.register('attempts', PracticeAttemptViewSet, basename='practice-attempt')

urlpatterns = [
    path('', include(router.urls)),
]

