"""
Views for Learning app.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrReadOnly
from .models import (
    Lesson,
    Unit,
    UnitWordDetail,
    UnitGrammarDetail,
    UnitKanjiDetail,
    UnitAnkiCard,
    UserUnitProgress,
)
from .serializers import (
    LessonSerializer,
    UnitSerializer,
    UnitAnkiReviewSerializer,
    UserUnitProgressSerializer,
)
from .anki import (
    apply_anki_review,
    ensure_unit_cards_for_user,
    get_next_card,
    get_unit_card_stats,
    serialize_card,
)

# Import serializers from other apps for unit detail
from apps.vocabulary.models import Word
from apps.vocabulary.serializers import WordSerializer
from apps.grammar.models import Grammar
from apps.grammar.serializers import GrammarSerializer
from apps.kanjis.models import Kanji
from apps.kanjis.serializers import KanjiSerializer


@extend_schema_view(
    list=extend_schema(description="List all lessons"),
    retrieve=extend_schema(description="Get a specific lesson"),
    create=extend_schema(description="Create a new lesson"),
    update=extend_schema(description="Update a lesson"),
    partial_update=extend_schema(description="Partially update a lesson"),
    destroy=extend_schema(description="Delete a lesson"),
)
class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for Lesson model."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lession_name']
    ordering_fields = ['id', 'lession_name', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    @extend_schema(
        description="Get all units of a lesson with summary counts",
        parameters=[
            OpenApiParameter(
                name='unit_type',
                description='Filter by unit type (vocabulary, grammar, kanji)',
                required=False,
                type=str
            ),
        ],
    )
    @action(detail=True, methods=['get'], url_path='units')
    def units(self, request, pk=None):
        """Get all units of a lesson with summary."""
        lesson = self.get_object()
        units = Unit.objects.filter(lession_id=str(lesson.id)).order_by('id')

        # Apply unit_type filter
        unit_type = request.query_params.get('unit_type')
        if unit_type:
            if unit_type == 'vocabulary':
                units = units.filter(unit_type__in=('vocabulary', 'word'))
            else:
                units = units.filter(unit_type=unit_type)

        # Calculate summary from all units (not filtered)
        all_units = Unit.objects.filter(lession_id=str(lesson.id))
        summary = {
            'total_units': all_units.count(),
            'vocabulary_units': all_units.filter(
                Q(unit_type='vocabulary') | Q(unit_type='word')
            ).count(),
            'grammar_units': all_units.filter(unit_type='grammar').count(),
            'kanji_units': all_units.filter(unit_type='kanji').count(),
        }

        page = self.paginate_queryset(units)
        if page is not None:
            serializer = UnitSerializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
            return Response({
                'lesson': LessonSerializer(lesson).data,
                'summary': summary,
                'count': paginated_data.get('count', units.count()),
                'next': paginated_data.get('next'),
                'previous': paginated_data.get('previous'),
                'units': paginated_data.get('results', []),
            })

        return Response({
            'lesson': LessonSerializer(lesson).data,
            'summary': summary,
            'units': UnitSerializer(units, many=True).data,
        })


@extend_schema_view(
    list=extend_schema(description="List all units"),
    retrieve=extend_schema(description="Get a specific unit"),
    create=extend_schema(description="Create a new unit"),
    update=extend_schema(description="Update a unit"),
    partial_update=extend_schema(description="Partially update a unit"),
    destroy=extend_schema(description="Delete a unit"),
)
class UnitViewSet(viewsets.ModelViewSet):
    """ViewSet for Unit model."""
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['unit_name', 'lession_id', 'unit_type']
    ordering_fields = ['id', 'unit_name', 'lession_id', 'created_at']
    ordering = ['id']

    @staticmethod
    def _to_bool(value, default=False):
        if value is None:
            return default
        return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    def get_queryset(self):
        queryset = super().get_queryset()
        lession_id = self.request.query_params.get('lession_id')
        if lession_id:
            queryset = queryset.filter(lession_id=lession_id)
        unit_type = self.request.query_params.get('unit_type')
        if unit_type:
            if unit_type == 'vocabulary':
                queryset = queryset.filter(unit_type__in=('vocabulary', 'word'))
            else:
                queryset = queryset.filter(unit_type=unit_type)
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    def get_permissions(self):
        # Units are a content resource: only admins can modify them, but all authenticated
        # users can read and use study-related actions (anki, detail).
        if self.action in {'create', 'update', 'partial_update', 'destroy'}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @extend_schema(
        description="Get unit detail with full content (words, grammar, or kanji)",
        parameters=[
            OpenApiParameter(
                name='page',
                description='Page number (default: 1)',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='page_size',
                description='Items per page (default: 20, max: 100)',
                required=False,
                type=int,
            ),
        ],
    )
    @action(detail=True, methods=['get'], url_path='detail')
    def detail_content(self, request, pk=None):
        """Get unit detail with full content based on unit type."""
        unit = self.get_object()
        queryset = None
        serializer_class = None

        if unit.unit_type in ('vocabulary', 'word'):
            # Get word IDs from junction table
            word_ids = list(UnitWordDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('word_id', flat=True))
            # Convert to integers and fetch words
            int_ids = [int(w) for w in word_ids if w and str(w).isdigit()]
            queryset = Word.objects.filter(id__in=int_ids).order_by('id')
            serializer_class = WordSerializer

        elif unit.unit_type == 'grammar':
            # Get grammar IDs from junction table
            grammar_ids = list(UnitGrammarDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('grammar_id', flat=True))
            # Convert to integers and fetch grammar
            int_ids = [int(g) for g in grammar_ids if g and g.isdigit()]
            queryset = Grammar.objects.filter(id__in=int_ids).order_by('id')
            serializer_class = GrammarSerializer

        elif unit.unit_type == 'kanji':
            # Get kanji IDs from junction table
            kanji_ids = list(UnitKanjiDetail.objects.filter(
                unit_id=str(unit.id)
            ).values_list('kanji_id', flat=True))
            # Convert to integers and fetch kanji
            int_ids = [int(k) for k in kanji_ids if k and k.isdigit()]
            queryset = Kanji.objects.filter(id__in=int_ids).order_by('id')
            serializer_class = KanjiSerializer

        queryset = queryset if queryset is not None else []

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True) if serializer_class else []
            paginated_data = self.get_paginated_response(serializer.data if serializer_class else []).data
            current_page = request.query_params.get('page', '1')
            try:
                current_page = int(current_page)
            except (TypeError, ValueError):
                current_page = 1
            page_size = self.paginator.get_page_size(request) if getattr(self, 'paginator', None) else None
            return Response({
                'unit': UnitSerializer(unit).data,
                'page': current_page,
                'page_size': page_size or len(page),
                'count': paginated_data.get('count', len(queryset) if isinstance(queryset, list) else queryset.count()),
                'next': paginated_data.get('next'),
                'previous': paginated_data.get('previous'),
                'items': paginated_data.get('results', []),
            })

        items = serializer_class(queryset, many=True).data if serializer_class else []

        return Response({
            'unit': UnitSerializer(unit).data,
            'page': 1,
            'page_size': len(items),
            'count': len(items),
            'next': None,
            'previous': None,
            'items': items
        })

    @extend_schema(
        description="Get next Anki card for the current user inside this unit.",
        parameters=[
            OpenApiParameter(
                name='include_future',
                description='If true, return nearest upcoming card when no card is currently due.',
                required=False,
                type=bool,
            ),
        ],
    )
    @action(detail=True, methods=['get'], url_path='anki/next')
    def anki_next(self, request, pk=None):
        unit = self.get_object()
        user_id = str(request.user.id)
        include_future = self._to_bool(request.query_params.get('include_future'), default=True)

        sync = ensure_unit_cards_for_user(unit=unit, user_id=user_id)
        card, is_due = get_next_card(unit_id=unit.id, user_id=user_id, include_future=include_future)
        stats = get_unit_card_stats(unit_id=unit.id, user_id=user_id)

        return Response({
            'unit': UnitSerializer(unit).data,
            'sync': sync,
            'card': serialize_card(card),
            'card_is_due': bool(card and is_due),
            'stats': stats,
        })

    @extend_schema(
        description="Submit review result for one Anki card (again/hard/good/easy).",
        request=UnitAnkiReviewSerializer,
    )
    @action(detail=True, methods=['post'], url_path='anki/review')
    def anki_review(self, request, pk=None):
        unit = self.get_object()
        user_id = str(request.user.id)
        serializer = UnitAnkiReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        ensure_unit_cards_for_user(unit=unit, user_id=user_id)

        card = UnitAnkiCard.objects.filter(
            id=payload['card_id'],
            unit_id=str(unit.id),
            user_id=user_id,
        ).first()
        if not card:
            raise ValidationError({'message': 'Card does not belong to this user or unit.'})

        reviewed_card = apply_anki_review(
            card=card,
            rating=payload['rating'],
            response_time_ms=payload.get('response_time_ms'),
        )
        next_card, is_due = get_next_card(unit_id=unit.id, user_id=user_id, include_future=True)
        stats = get_unit_card_stats(unit_id=unit.id, user_id=user_id)

        return Response({
            'unit': UnitSerializer(unit).data,
            'reviewed_card': serialize_card(reviewed_card),
            'next_card': serialize_card(next_card),
            'next_card_is_due': bool(next_card and is_due),
            'stats': stats,
        })

    @extend_schema(
        description="Get Anki scheduling stats for the current user in this unit.",
    )
    @action(detail=True, methods=['get'], url_path='anki/stats')
    def anki_stats(self, request, pk=None):
        unit = self.get_object()
        user_id = str(request.user.id)
        sync = ensure_unit_cards_for_user(unit=unit, user_id=user_id)
        stats = get_unit_card_stats(unit_id=unit.id, user_id=user_id)

        return Response({
            'unit': UnitSerializer(unit).data,
            'sync': sync,
            'stats': stats,
        })





@extend_schema_view(
    list=extend_schema(description="List all user unit progress records"),
    retrieve=extend_schema(description="Get a specific user unit progress"),
    create=extend_schema(description="Create a new user unit progress"),
    update=extend_schema(description="Update a user unit progress"),
    partial_update=extend_schema(description="Partially update a user unit progress"),
    destroy=extend_schema(description="Delete a user unit progress"),
)
class UserUnitProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for UserUnitProgress model."""
    queryset = UserUnitProgress.objects.all()
    serializer_class = UserUnitProgressSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'unit_id', 'lession_id', 'user_id', 'progress']
    ordering = ['id']

    def _is_admin(self):
        user = self.request.user
        return bool(user and (user.is_staff or user.is_superuser))

    @staticmethod
    def _parse_progress(value) -> float | None:
        """
        Progress is stored as a TextField (historical import). Accept numbers or numeric strings.
        Returns float or None if unparseable.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        raw = str(value).strip()
        if not raw:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _progress_is_completed(self, value) -> bool:
        # Treat 100+ as completed, per frontend integration guide.
        v = self._parse_progress(value)
        return bool(v is not None and v >= 100)

    def _update_user_streak_if_needed(self, user) -> None:
        """
        Update streak when the user completes at least one unit on a new calendar day.

        Rules:
        - If last_study_date is today: keep streak unchanged.
        - If last_study_date is yesterday: increment streak.
        - Otherwise: reset streak to 1.
        """
        today = timezone.now().date()
        last = user.last_study_date
        if last == today:
            return

        if last == (today - timedelta(days=1)):
            user.streak = int(user.streak or 0) + 1
        else:
            user.streak = 1
        user.last_study_date = today
        user.save(update_fields=['streak', 'last_study_date'])

    def get_queryset(self):
        queryset = super().get_queryset()

        # Non-admin users can only access their own progress records.
        if not self._is_admin():
            queryset = queryset.filter(user_id=str(self.request.user.id))

        user_id = self.request.query_params.get('user_id')
        if user_id and self._is_admin():
            queryset = queryset.filter(user_id=user_id)
        unit_id = self.request.query_params.get('unit_id')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        lession_id = self.request.query_params.get('lession_id')
        if lession_id:
            queryset = queryset.filter(lession_id=lession_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Upsert progress for (user_id, unit_id).

        This matches the frontend expectation: client often only knows unit_id and sends POST repeatedly.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Determine target user_id. Non-admin users can only write their own progress.
        target_user_id = str(request.user.id)
        if self._is_admin() and data.get('user_id'):
            target_user_id = str(data.get('user_id')).strip()

        unit_id = str(data.get('unit_id') or '').strip()
        if not unit_id:
            raise ValidationError({'unit_id': 'This field is required.'})

        # Find latest record if duplicates exist (historical data). Update the newest one.
        qs = UserUnitProgress.objects.filter(user_id=target_user_id, unit_id=unit_id).order_by('-id')
        instance = qs.first()
        created = instance is None
        if created:
            instance = UserUnitProgress(user_id=target_user_id, unit_id=unit_id)

        was_completed = bool(getattr(instance, 'completed_at', None))

        # Update fields.
        if data.get('lession_id') is not None:
            instance.lession_id = str(data.get('lession_id') or '').strip()
        if data.get('progress') is not None:
            instance.progress = str(data.get('progress'))

        now_completed = was_completed or self._progress_is_completed(instance.progress)
        if now_completed and not was_completed:
            instance.completed_at = timezone.now().isoformat()

        instance.user_id = target_user_id
        instance.save()

        # Update user's streak on first completion transition for this unit.
        if now_completed and not was_completed:
            UserModel = get_user_model()
            try:
                user_obj = UserModel.objects.get(id=int(target_user_id))
            except Exception:
                user_obj = None
            if user_obj is not None:
                self._update_user_streak_if_needed(user_obj)

        out = self.get_serializer(instance)
        return Response(out.data, status=(201 if created else 200))

    def perform_create(self, serializer):
        if self._is_admin() and serializer.validated_data.get('user_id'):
            serializer.save()
            return
        serializer.save(user_id=str(self.request.user.id))

    def perform_update(self, serializer):
        instance = self.get_object()
        was_completed = bool(getattr(instance, 'completed_at', None))

        if self._is_admin():
            updated = serializer.save()
        else:
            updated = serializer.save(user_id=str(self.request.user.id))

        now_completed = was_completed or self._progress_is_completed(getattr(updated, 'progress', None))
        if now_completed and not was_completed:
            updated.completed_at = updated.completed_at or timezone.now().isoformat()
            updated.save(update_fields=['completed_at', 'updated_at'])

            # Best-effort streak update.
            UserModel = get_user_model()
            try:
                user_obj = UserModel.objects.get(id=int(updated.user_id))
            except Exception:
                user_obj = None
            if user_obj is not None:
                self._update_user_streak_if_needed(user_obj)
