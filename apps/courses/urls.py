"""
URL patterns for Courses app.
"""
from django.urls import path

from .views import CoursePlaceholderView

app_name = 'courses'

urlpatterns = [
    path('', CoursePlaceholderView.as_view(), name='placeholder'),
]
