# JLPT Lessons & Units Creation Plan

## Overview

Tạo hệ thống Lessons và Units cho các cấp độ JLPT từ N5 đến N1. Mỗi level JLPT sẽ là 1 Lesson, và các Units sẽ được chia theo loại (vocabulary, grammar, kanji) với số lượng item cố định cho mỗi unit.

**Project Type:** BACKEND

## Success Criteria

- [ ] 5 Lessons mới được tạo (N5, N4, N3, N2, N1)
- [ ] All Units được tạo với đúng số lượng items (20 words, 5 kanji, 3 grammar)
- [ ] UnitWordDetail, UnitGrammarDetail, UnitKanjiDetail có dữ liệu cho tất cả units
- [ ] API `/api/learning/units/` có thêm filter `level`
- [ ] Management command hoạt động ổn định
- [ ] Lesson "Beginner" giữ nguyên không bị ảnh hưởng

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Django + DRF | Existing stack |
| Database | PostgreSQL | Existing setup |
| ORM | Django ORM | Leveraging existing models |
| Script | Django Management Command | Best practice for data seeding |

---

## Data Analysis

### Current Data Counts

| Level | Words | Grammar | Kanji |
|-------|-------|---------|-------|
| N5 | 1,985 | 119 | 160 |
| N4 | 1,861 | 177 | 250 |
| N3 | 4,411 | 216 | 570 |
| N2 | 3,522 | 210 | 546 |
| N1 | 5,287 | 179 | 1,456 |

### Planned Units (per level)

| Level | Word Units (20/unit) | Grammar Units (3/unit) | Kanji Units (5/unit) | Total Units |
|-------|---------------------|------------------------|---------------------|-------------|
| N5 | 100 | 40 | 32 | 172 |
| N4 | 93 | 59 | 50 | 202 |
| N3 | 221 | 72 | 114 | 407 |
| N2 | 176 | 70 | 110 | 356 |
| N1 | 265 | 60 | 292 | 617 |
| **TOTAL** | **855** | **301** | **598** | **1,754** |

### Unit Naming Convention

- **Word Unit:** `N5 - Từ vựng - Bài 1`, `N5 - Từ vựng - Bài 2`, ...
- **Grammar Unit:** `N5 - Ngữ pháp - Bài 1`, `N5 - Ngữ pháp - Bài 2`, ...
- **Kanji Unit:** `N5 - Hán tự - Bài 1`, `N5 - Hán tự - Bài 2`, ...

---

## Proposed Changes

### 1. Model Enhancement

#### [MODIFY] [models.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/models.py)

Thêm field `level` vào model `Lesson` và `Unit` để hỗ trợ filter theo level:

```python
# In Lesson model
level = models.CharField(
    'JLPT level',
    max_length=5,
    blank=True,
    null=True,
    help_text='JLPT level (N5, N4, N3, N2, N1)'
)

# In Unit model
level = models.CharField(
    'JLPT level',
    max_length=5,
    blank=True,
    null=True,
    help_text='JLPT level (N5, N4, N3, N2, N1)'
)
```

---

### 2. API Enhancement

#### [MODIFY] [views.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/views.py)

Thêm filter `level` vào `UnitViewSet.get_queryset()`:

```python
def get_queryset(self):
    queryset = super().get_queryset()
    lession_id = self.request.query_params.get('lession_id')
    if lession_id:
        queryset = queryset.filter(lession_id=lession_id)
    unit_type = self.request.query_params.get('unit_type')
    if unit_type:
        queryset = queryset.filter(unit_type=unit_type)
    # NEW: Add level filter
    level = self.request.query_params.get('level')
    if level:
        queryset = queryset.filter(level=level)
    return queryset
```

Thêm filter `level` vào `LessonViewSet.get_queryset()`:

```python
def get_queryset(self):
    queryset = super().get_queryset()
    level = self.request.query_params.get('level')
    if level:
        queryset = queryset.filter(level=level)
    return queryset
```

---

### 3. Management Command

#### [NEW] [create_jlpt_lessons.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/management/commands/create_jlpt_lessons.py)

Django management command để tạo Lessons và Units:

**Chức năng:**
1. Tạo 5 Lessons (N5, N4, N3, N2, N1)
2. Với mỗi Lesson, tạo Units theo 3 loại:
   - Vocabulary Units (20 words/unit)
   - Grammar Units (3 grammar/unit)
   - Kanji Units (5 kanji/unit)
3. Tạo UnitWordDetail, UnitGrammarDetail, UnitKanjiDetail

**Arguments:**
- `--level`: Chỉ tạo cho level cụ thể (N5, N4, N3, N2, N1)
- `--type`: Chỉ tạo cho type cụ thể (vocabulary, grammar, kanji)
- `--dry-run`: Chạy thử không lưu vào DB

**Algorithm:**
```
FOR each level in [N5, N4, N3, N2, N1]:
    1. CREATE Lesson with name = "JLPT {level}"

    2. FETCH all Words where level = {level} ORDER BY id
       CHUNK into groups of 20
       FOR each chunk:
           CREATE Unit "N{level} - Từ vựng - Bài {n}"
           CREATE UnitWordDetail for each word

    3. FETCH all Grammar where level = {level_int} ORDER BY id
       CHUNK into groups of 3
       FOR each chunk:
           CREATE Unit "N{level} - Ngữ pháp - Bài {n}"
           CREATE UnitGrammarDetail for each grammar

    4. FETCH all Kanji where level = {level_int} ORDER BY id
       CHUNK into groups of 5
       FOR each chunk:
           CREATE Unit "N{level} - Hán tự - Bài {n}"
           CREATE UnitKanjiDetail for each kanji
```

---

## File Structure

```
apps/learning/
├── management/
│   └── commands/
│       └── create_jlpt_lessons.py  # [NEW] Management command
├── models.py                        # [MODIFY] Add level field
├── views.py                         # [MODIFY] Add level filter
├── serializers.py                   # [MODIFY] Add level to serializer (if needed)
└── migrations/
    └── XXXX_add_level_fields.py     # [NEW] Auto-generated migration
```

---

## Task Breakdown

### Phase 1: Model Enhancement
| Task | Agent | Skill | Priority | Dependencies |
|------|-------|-------|----------|--------------|
| 1.1 Add `level` field to Lesson model | backend-specialist | database-design | P0 | - |
| 1.2 Add `level` field to Unit model | backend-specialist | database-design | P0 | - |
| 1.3 Create migration | backend-specialist | database-design | P0 | 1.1, 1.2 |
| 1.4 Run migration | backend-specialist | database-design | P0 | 1.3 |

**INPUT:** Current models without level field
**OUTPUT:** Models with level field, migration applied
**VERIFY:** `python manage.py showmigrations` shows new migration applied

---

### Phase 2: Serializer Update
| Task | Agent | Skill | Priority | Dependencies |
|------|-------|-------|----------|--------------|
| 2.1 Add `level` to LessonSerializer | backend-specialist | api-patterns | P1 | Phase 1 |
| 2.2 Add `level` to UnitSerializer | backend-specialist | api-patterns | P1 | Phase 1 |

**INPUT:** Serializers without level field
**OUTPUT:** Serializers with level field
**VERIFY:** API response includes `level` field

---

### Phase 3: API Enhancement
| Task | Agent | Skill | Priority | Dependencies |
|------|-------|-------|----------|--------------|
| 3.1 Add level filter to LessonViewSet | backend-specialist | api-patterns | P1 | Phase 2 |
| 3.2 Add level filter to UnitViewSet | backend-specialist | api-patterns | P1 | Phase 2 |

**INPUT:** Views without level filter
**OUTPUT:** Views with level filter
**VERIFY:** `GET /api/learning/units/?level=N5` returns only N5 units

---

### Phase 4: Management Command
| Task | Agent | Skill | Priority | Dependencies |
|------|-------|-------|----------|--------------|
| 4.1 Create management command structure | backend-specialist | python-patterns | P2 | Phase 1 |
| 4.2 Implement Lesson creation logic | backend-specialist | python-patterns | P2 | 4.1 |
| 4.3 Implement Vocabulary Unit creation | backend-specialist | python-patterns | P2 | 4.2 |
| 4.4 Implement Grammar Unit creation | backend-specialist | python-patterns | P2 | 4.2 |
| 4.5 Implement Kanji Unit creation | backend-specialist | python-patterns | P2 | 4.2 |
| 4.6 Add progress bar and logging | backend-specialist | python-patterns | P3 | 4.3, 4.4, 4.5 |

**INPUT:** Empty management command
**OUTPUT:** Working management command
**VERIFY:** `python manage.py create_jlpt_lessons --dry-run` shows expected output

---

### Phase 5: Data Seeding
| Task | Agent | Skill | Priority | Dependencies |
|------|-------|-------|----------|--------------|
| 5.1 Run command for N5 | backend-specialist | - | P2 | Phase 4 |
| 5.2 Run command for N4 | backend-specialist | - | P2 | 5.1 |
| 5.3 Run command for N3 | backend-specialist | - | P2 | 5.2 |
| 5.4 Run command for N2 | backend-specialist | - | P2 | 5.3 |
| 5.5 Run command for N1 | backend-specialist | - | P2 | 5.4 |

**INPUT:** Empty Lessons/Units tables (except Beginner)
**OUTPUT:** All 1,754 Units with details created
**VERIFY:**
- `Lesson.objects.count()` = 6 (Beginner + 5 JLPT levels)
- `Unit.objects.count()` ≈ 1,754 + existing units

---

## Phase X: Verification

### Automated Tests
```bash
# Check migrations
python manage.py showmigrations learning

# Check data counts
python manage.py shell -c "
from apps.learning.models import Lesson, Unit, UnitWordDetail, UnitGrammarDetail, UnitKanjiDetail
print(f'Lessons: {Lesson.objects.count()}')
print(f'Units: {Unit.objects.count()}')
print(f'Word Details: {UnitWordDetail.objects.count()}')
print(f'Grammar Details: {UnitGrammarDetail.objects.count()}')
print(f'Kanji Details: {UnitKanjiDetail.objects.count()}')
"

# Test API filters
curl "http://localhost:8000/api/learning/lessons/?level=N5"
curl "http://localhost:8000/api/learning/units/?level=N5&unit_type=vocabulary"
```

### Manual Verification
- [ ] Lesson "Beginner" vẫn tồn tại và không bị ảnh hưởng
- [ ] 5 Lessons mới (N5-N1) được tạo đúng
- [ ] Mỗi Unit có đúng số lượng items
- [ ] API filter hoạt động đúng

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data seeding takes too long | Medium | Use bulk_create, add progress bar |
| Duplicate data if run twice | High | Add check for existing lessons before creating |
| Memory issues with large data | Medium | Process in batches |

---

## Rollback Strategy

```bash
# If something goes wrong, delete new data:
python manage.py shell -c "
from apps.learning.models import Lesson, Unit

# Delete new lessons and their units
for level in ['N5', 'N4', 'N3', 'N2', 'N1']:
    lesson = Lesson.objects.filter(lession_name__startswith=f'JLPT {level}').first()
    if lesson:
        Unit.objects.filter(lession_id=str(lesson.id)).delete()
        lesson.delete()
"
```

---

## Estimated Time

| Phase | Estimated Time |
|-------|---------------|
| Phase 1: Model Enhancement | 10 mins |
| Phase 2: Serializer Update | 5 mins |
| Phase 3: API Enhancement | 10 mins |
| Phase 4: Management Command | 30 mins |
| Phase 5: Data Seeding | 20 mins |
| Phase X: Verification | 10 mins |
| **TOTAL** | **~85 mins** |
