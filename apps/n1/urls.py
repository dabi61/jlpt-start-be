"""URL patterns for N1 practice APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    N1SectionViewSet,
    N1SubcategoryViewSet,
    N1ExamViewSet,
    N1QuestionViewSet,
    N1QuestionItemViewSet,
    N1MediaAssetViewSet,
)

app_name = 'n1'

router = DefaultRouter()
router.register('sections', N1SectionViewSet, basename='n1-section')
router.register('subcategories', N1SubcategoryViewSet, basename='n1-subcategory')
router.register('exams', N1ExamViewSet, basename='n1-exam')
router.register('questions', N1QuestionViewSet, basename='n1-question')
router.register('question-items', N1QuestionItemViewSet, basename='n1-question-item')
router.register('media-assets', N1MediaAssetViewSet, basename='n1-media-asset')

urlpatterns = [
    path('', include(router.urls)),
]
