"""
URL patterns for Learning app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LessonViewSet,
    UnitViewSet,
    UnitWordDetailViewSet,
    UnitGrammarDetailViewSet,
    UnitKanjiDetailViewSet,
    UserUnitProgressViewSet,
    BookSetViewSet,
    BookSetUnitViewSet,
    BookSetUnitDetailViewSet,
)

app_name = 'learning'

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'unit-words', UnitWordDetailViewSet, basename='unit-word')
router.register(r'unit-grammars', UnitGrammarDetailViewSet, basename='unit-grammar')
router.register(r'unit-kanjis', UnitKanjiDetailViewSet, basename='unit-kanji')
router.register(r'progress', UserUnitProgressViewSet, basename='progress')
router.register(r'book-sets', BookSetViewSet, basename='book-set')
router.register(r'book-set-units', BookSetUnitViewSet, basename='book-set-unit')
router.register(r'book-set-unit-details', BookSetUnitDetailViewSet, basename='book-set-unit-detail')

urlpatterns = [
    path('', include(router.urls)),
]
