# BookSet Migration to Lesson/Unit Plan

## Overview

Migrate dữ liệu từ các bảng `BookSet`, `BookSetUnit`, `BookSetUnitDetail` sang hệ thống `Lesson`, `Unit`, `UnitWordDetail` hiện có.

**Project Type:** BACKEND (Data Migration)

## Current BookSet Data

| ID | Book Name | Level | Total Words | Units |
|----|-----------|-------|-------------|-------|
| 1 | MimiKara | N1 | 1,169 | 13 |
| 2 | MimiKara | N2 | 1,167 | 89 |
| 3 | MimiKara | N3 | 880 | 66 |
| 4 | Soumatome | N1 | 1,499 | 47 |
| 5 | Soumatome | N2 | 2,176 | 48 |
| 6 | Soumatome | N3 | 1,345 | 36 |
| 7 | Soumatome | N4 | 821 | 20 |
| 8 | Shinkanzen | N1 | 958 | 49 |
| 9 | Shinkanzen | N2 | 1,679 | 42 |
| 10 | Shinkanzen | N3 | 1,798 | 63 |
| 11 | Shinkanzen | N4 | 688 | 50 |
| 12 | N5 tango | N5 | 1,293 | 50 |

**Total:** 12 BookSets → 573 BookSetUnits → 15,602 BookSetUnitDetails

---

## Migration Strategy

### Mapping Logic

| BookSet | → | Lesson |
|---------|---|--------|
| `BookSet.name` | → | `Lesson.lession_name` (e.g., "MimiKara N1") |
| `BookSet.level` (1-5) | → | `Lesson.level` (N1-N5) |

| BookSetUnit | → | Unit |
|-------------|---|------|
| `BookSetUnit.name` | → | `Unit.unit_name` (e.g., "MimiKara N1 - Bài 1") |
| `BookSetUnit.book_set_id` | → | `Unit.lession_id` (new Lesson ID) |
| `BookSetUnit.total_word` | → | `Unit.total` |
| - | → | `Unit.unit_type = 'vocabulary'` |
| - | → | `Unit.level` (from parent Lesson) |

| BookSetUnitDetail | → | UnitWordDetail |
|-------------------|---|----------------|
| `BookSetUnitDetail.unit_id` | → | `UnitWordDetail.unit_id` (new Unit ID) |
| `BookSetUnitDetail.word_id` | → | `UnitWordDetail.word_id` |

---

## Proposed Changes

### Phase 1: Create Migration Command

#### [NEW] [migrate_bookset_to_lessons.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/management/commands/migrate_bookset_to_lessons.py)

Django management command to:
1. Read all BookSets
2. Create corresponding Lessons (with name like "MimiKara N1")
3. Create Units from BookSetUnits
4. Create UnitWordDetails from BookSetUnitDetails

```python
# Key logic:
for bookset in BookSet.objects.all():
    level_map = {'1': 'N1', '2': 'N2', '3': 'N3', '4': 'N4', '5': 'N5'}
    level = level_map.get(bookset.level, '')

    lesson = Lesson.objects.create(
        lession_name=f"{bookset.name} {level}",
        level=level
    )

    for bsu in BookSetUnit.objects.filter(book_set_id=str(bookset.id)):
        unit = Unit.objects.create(
            unit_name=f"{bookset.name} {level} - {bsu.name}",
            lession_id=str(lesson.id),
            total=bsu.total_word,
            unit_type='vocabulary',
            level=level
        )

        # Migrate word details
        details = BookSetUnitDetail.objects.filter(unit_id=str(bsu.id))
        for detail in details:
            UnitWordDetail.objects.create(
                unit_id=str(unit.id),
                word_id=detail.word_id
            )
```

**Command options:**
- `--dry-run`: Preview only, no data changes
- `--bookset-id=<id>`: Migrate specific bookset only

---

## Task Breakdown

### Phase 1: Migration Command
| Task | Priority | Est. Time |
|------|----------|-----------|
| 1.1 Create management command file | P0 | 10 min |
| 1.2 Implement BookSet → Lesson migration | P0 | 10 min |
| 1.3 Implement BookSetUnit → Unit migration | P0 | 10 min |
| 1.4 Implement BookSetUnitDetail → UnitWordDetail migration | P0 | 10 min |
| 1.5 Add dry-run support | P1 | 5 min |

### Phase 2: Run Migration
| Task | Priority | Est. Time |
|------|----------|-----------|
| 2.1 Run dry-run to verify | P0 | 5 min |
| 2.2 Execute full migration | P0 | 5 min |

---

## Expected Result After Migration

| Type | Before | After |
|------|--------|-------|
| Lessons | 6 (Beginner + 5 JLPT) | 18 (+12 BookSet lessons) |
| Units | 1,806 | 2,379 (+573 BookSet units) |
| UnitWordDetails | 19,118 | 34,720 (+15,602 from BookSet) |

---

## Phase X: Verification

### Automated Tests
```bash
# Dry-run first
docker compose exec web python manage.py migrate_bookset_to_lessons --dry-run

# After migration - verify counts
docker compose exec web python manage.py shell -c "
from apps.learning.models import Lesson, Unit, UnitWordDetail
print(f'Lessons: {Lesson.objects.count()}')
print(f'Units: {Unit.objects.count()}')
print(f'UnitWordDetails: {UnitWordDetail.objects.count()}')
"
```

### Manual Verification
1. Check API returns new lessons:
   ```bash
   curl "http://localhost:8000/api/learning/lessons/"
   ```

2. Check MimiKara N1 lesson has 13 units:
   ```bash
   curl "http://localhost:8000/api/learning/lessons/<id>/units/"
   ```

3. Check unit detail returns words:
   ```bash
   curl "http://localhost:8000/api/learning/units/<id>/detail/"
   ```

---

## Estimated Time

| Phase | Time |
|-------|------|
| Phase 1: Create Command | 45 min |
| Phase 2: Run Migration | 10 min |
| Phase X: Verification | 10 min |
| **TOTAL** | **~65 min** |

---

## Rollback Strategy

Nếu cần rollback, có thể xóa các Lessons mới tạo:

```python
# Xóa các lesson từ BookSet (ID > 7 vì 1-7 là Beginner + JLPT)
Lesson.objects.filter(id__gt=7).delete()
```
