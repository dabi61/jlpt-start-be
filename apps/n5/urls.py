"""URL patterns for N5 practice APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    N5SectionViewSet,
    N5SubcategoryViewSet,
    N5ExamViewSet,
    N5QuestionViewSet,
    N5QuestionItemViewSet,
    N5MediaAssetViewSet,
)

app_name = 'n5'

router = DefaultRouter()
router.register('sections', N5SectionViewSet, basename='n5-section')
router.register('subcategories', N5SubcategoryViewSet, basename='n5-subcategory')
router.register('exams', N5ExamViewSet, basename='n5-exam')
router.register('questions', N5QuestionViewSet, basename='n5-question')
router.register('question-items', N5QuestionItemViewSet, basename='n5-question-item')
router.register('media-assets', N5MediaAssetViewSet, basename='n5-media-asset')

urlpatterns = [
    path('', include(router.urls)),
]
