"""URL patterns for N4 practice APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    N4SectionViewSet,
    N4SubcategoryViewSet,
    N4ExamViewSet,
    N4QuestionViewSet,
    N4QuestionItemViewSet,
    N4MediaAssetViewSet,
)

app_name = 'n4'

router = DefaultRouter()
router.register('sections', N4SectionViewSet, basename='n4-section')
router.register('subcategories', N4SubcategoryViewSet, basename='n4-subcategory')
router.register('exams', N4ExamViewSet, basename='n4-exam')
router.register('questions', N4QuestionViewSet, basename='n4-question')
router.register('question-items', N4QuestionItemViewSet, basename='n4-question-item')
router.register('media-assets', N4MediaAssetViewSet, basename='n4-media-asset')

urlpatterns = [
    path('', include(router.urls)),
]
