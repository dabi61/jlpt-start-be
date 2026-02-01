"""
URL patterns for Learning app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LessonViewSet,
    UnitViewSet,

    UserUnitProgressViewSet,
)

app_name = 'learning'

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'units', UnitViewSet, basename='unit')

router.register(r'progress', UserUnitProgressViewSet, basename='progress')

urlpatterns = [
    path('', include(router.urls)),
]
