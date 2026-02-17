"""URL patterns for N3 practice APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    N3SectionViewSet,
    N3SubcategoryViewSet,
    N3ExamViewSet,
    N3QuestionViewSet,
    N3QuestionItemViewSet,
    N3MediaAssetViewSet,
)

app_name = 'n3'

router = DefaultRouter()
router.register('sections', N3SectionViewSet, basename='n3-section')
router.register('subcategories', N3SubcategoryViewSet, basename='n3-subcategory')
router.register('exams', N3ExamViewSet, basename='n3-exam')
router.register('questions', N3QuestionViewSet, basename='n3-question')
router.register('question-items', N3QuestionItemViewSet, basename='n3-question-item')
router.register('media-assets', N3MediaAssetViewSet, basename='n3-media-asset')

urlpatterns = [
    path('', include(router.urls)),
]
