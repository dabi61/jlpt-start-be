"""URL patterns for N2 practice APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    N2SectionViewSet,
    N2SubcategoryViewSet,
    N2ExamViewSet,
    N2QuestionViewSet,
    N2QuestionItemViewSet,
    N2MediaAssetViewSet,
)

app_name = 'n2'

router = DefaultRouter()
router.register('sections', N2SectionViewSet, basename='n2-section')
router.register('subcategories', N2SubcategoryViewSet, basename='n2-subcategory')
router.register('exams', N2ExamViewSet, basename='n2-exam')
router.register('questions', N2QuestionViewSet, basename='n2-question')
router.register('question-items', N2QuestionItemViewSet, basename='n2-question-item')
router.register('media-assets', N2MediaAssetViewSet, basename='n2-media-asset')

urlpatterns = [
    path('', include(router.urls)),
]
