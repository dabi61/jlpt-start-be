# Lesson Units & Unit Detail API Plan

## Overview

Tạo 2 API endpoints mới:
1. **GET Lesson Summary**: Lấy tất cả units của 1 lesson kèm thống kê (vocab/kanji/grammar counts)
2. **GET Unit Detail**: Lấy nội dung chi tiết của 1 unit (danh sách words/grammar/kanji đầy đủ)

**Project Type:** BACKEND

## Success Criteria

- [ ] API `GET /api/learning/lessons/{id}/units/` trả về danh sách units với summary
- [ ] API `GET /api/learning/units/{id}/detail/` trả về nội dung chi tiết của unit
- [ ] Response bao gồm đầy đủ thông tin word/grammar/kanji
- [ ] API documentation (Swagger) được cập nhật

---

## Proposed API Design

### 1. Lesson Units Summary

**Endpoint:** `GET /api/learning/lessons/{lesson_id}/units/`

**Response:**
```json
{
  "lesson": {
    "id": 3,
    "name": "JLPT N5",
    "level": "N5"
  },
  "summary": {
    "total_units": 172,
    "vocabulary_units": 100,
    "grammar_units": 40,
    "kanji_units": 32
  },
  "units": [
    {
      "id": 51,
      "unit_name": "N5 - Từ vựng - Bài 1",
      "unit_type": "vocabulary",
      "total": 20
    },
    {
      "id": 52,
      "unit_name": "N5 - Từ vựng - Bài 2",
      "unit_type": "vocabulary",
      "total": 20
    }
    // ... more units
  ]
}
```

**Query Parameters:**
- `?unit_type=vocabulary` - Filter by type
- `?page=1&page_size=20` - Pagination

---

### 2. Unit Detail

**Endpoint:** `GET /api/learning/units/{unit_id}/detail/`

**Response for Vocabulary Unit:**
```json
{
  "unit": {
    "id": 51,
    "unit_name": "N5 - Từ vựng - Bài 1",
    "unit_type": "vocabulary",
    "level": "N5",
    "total": 20
  },
  "items": [
    {
      "id": 52317,
      "j_word": "あう",
      "phonetic": "あう",
      "short_mean": "gặp",
      "han": "会う",
      "level": "N5",
      "mean": [...]
    },
    // ... 19 more words
  ]
}
```

**Response for Grammar Unit:**
```json
{
  "unit": {
    "id": 151,
    "unit_name": "N5 - Ngữ pháp - Bài 1",
    "unit_type": "grammar",
    "level": "N5",
    "total": 3
  },
  "items": [
    {
      "id": 1,
      "title": "あれ",
      "mean": "đó, kia",
      "level": 5,
      "structure": "...",
      "examples": [...]
    },
    // ... 2 more grammar points
  ]
}
```

**Response for Kanji Unit:**
```json
{
  "unit": {
    "id": 251,
    "unit_name": "N5 - Hán tự - Bài 1",
    "unit_type": "kanji",
    "level": "N5",
    "total": 5
  },
  "items": [
    {
      "id": 1,
      "kanji": "一",
      "mean": "một",
      "on": "イチ",
      "kun": "ひと",
      "stroke_count": 1,
      "examples": [...]
    },
    // ... 4 more kanji
  ]
}
```

---

## Proposed Changes

### 1. Serializers

#### [MODIFY] [serializers.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/serializers.py)

Thêm serializers mới:

```python
class LessonUnitsSummarySerializer(serializers.Serializer):
    """Serializer for lesson units summary."""
    lesson = LessonSerializer()
    summary = serializers.DictField()
    units = UnitSerializer(many=True)


class UnitDetailSerializer(serializers.Serializer):
    """Serializer for unit detail with full content."""
    unit = UnitSerializer()
    items = serializers.ListField()
```

---

### 2. Views

#### [MODIFY] [views.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/views.py)

Thêm 2 action methods:

**LessonViewSet:**
```python
@action(detail=True, methods=['get'], url_path='units')
def units(self, request, pk=None):
    """Get all units of a lesson with summary."""
    lesson = self.get_object()
    units = Unit.objects.filter(lession_id=str(lesson.id))

    # Apply filters
    unit_type = request.query_params.get('unit_type')
    if unit_type:
        units = units.filter(unit_type=unit_type)

    # Calculate summary
    summary = {
        'total_units': units.count(),
        'vocabulary_units': units.filter(unit_type='vocabulary').count(),
        'grammar_units': units.filter(unit_type='grammar').count(),
        'kanji_units': units.filter(unit_type='kanji').count(),
    }

    return Response({
        'lesson': LessonSerializer(lesson).data,
        'summary': summary,
        'units': UnitSerializer(units, many=True).data
    })
```

**UnitViewSet:**
```python
@action(detail=True, methods=['get'], url_path='detail')
def detail_content(self, request, pk=None):
    """Get unit detail with full content."""
    unit = self.get_object()
    items = []

    if unit.unit_type == 'vocabulary':
        word_ids = UnitWordDetail.objects.filter(
            unit_id=str(unit.id)
        ).values_list('word_id', flat=True)
        items = Word.objects.filter(id__in=[int(w) for w in word_ids])
        items = WordSerializer(items, many=True).data

    elif unit.unit_type == 'grammar':
        grammar_ids = UnitGrammarDetail.objects.filter(
            unit_id=str(unit.id)
        ).values_list('grammar_id', flat=True)
        items = Grammar.objects.filter(id__in=[int(g) for g in grammar_ids])
        items = GrammarSerializer(items, many=True).data

    elif unit.unit_type == 'kanji':
        kanji_ids = UnitKanjiDetail.objects.filter(
            unit_id=str(unit.id)
        ).values_list('kanji_id', flat=True)
        items = Kanji.objects.filter(id__in=[int(k) for k in kanji_ids])
        items = KanjiSerializer(items, many=True).data

    return Response({
        'unit': UnitSerializer(unit).data,
        'items': items
    })
```

---

## File Structure

```
apps/learning/
├── views.py        # [MODIFY] Add 2 action methods
├── serializers.py  # [MODIFY] Add summary serializers (optional)
└── urls.py         # [NO CHANGE] Router auto-registers actions
```

---

## Task Breakdown

### Phase 1: Lesson Units Summary API
| Task | Priority | Dependencies |
|------|----------|--------------|
| 1.1 Add `units` action to LessonViewSet | P0 | - |
| 1.2 Implement unit filtering and summary | P0 | 1.1 |
| 1.3 Add pagination support | P1 | 1.1 |

**INPUT:** LessonViewSet without units action
**OUTPUT:** `GET /lessons/{id}/units/` endpoint working
**VERIFY:** `curl localhost:8000/api/learning/lessons/3/units/`

---

### Phase 2: Unit Detail API
| Task | Priority | Dependencies |
|------|----------|--------------|
| 2.1 Add `detail_content` action to UnitViewSet | P0 | - |
| 2.2 Implement vocabulary content fetch | P0 | 2.1 |
| 2.3 Implement grammar content fetch | P0 | 2.1 |
| 2.4 Implement kanji content fetch | P0 | 2.1 |

**INPUT:** UnitViewSet without detail action
**OUTPUT:** `GET /units/{id}/detail/` endpoint working
**VERIFY:** `curl localhost:8000/api/learning/units/51/detail/`

---

## Phase X: Verification

### API Tests
```bash
# Test lesson units summary
curl "http://localhost:8000/api/learning/lessons/3/units/"
curl "http://localhost:8000/api/learning/lessons/3/units/?unit_type=vocabulary"

# Test unit detail
curl "http://localhost:8000/api/learning/units/51/detail/"  # vocabulary
curl "http://localhost:8000/api/learning/units/151/detail/" # grammar
curl "http://localhost:8000/api/learning/units/251/detail/" # kanji
```

### Checklist
- [ ] Lesson units summary returns correct counts
- [ ] Unit detail returns full word/grammar/kanji data
- [ ] Filtering by unit_type works
- [ ] Swagger documentation shows new endpoints

---

## Estimated Time

| Phase | Estimated Time |
|-------|---------------|
| Phase 1: Lesson Units Summary | 15 mins |
| Phase 2: Unit Detail | 20 mins |
| Phase X: Verification | 10 mins |
| **TOTAL** | **~45 mins** |
