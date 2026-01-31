"""
URL patterns for Examples app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ExampleViewSet

app_name = 'examples'

router = DefaultRouter()
router.register('', ExampleViewSet, basename='example')

urlpatterns = router.urls
