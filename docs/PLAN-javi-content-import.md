# Javi Content Import & BookSet Mapping Plan

## Overview

Import dữ liệu từ `javi_content.json` vào bảng `Word`, sau đó re-map `UnitWordDetail` để sử dụng đúng Word IDs.

**Project Type:** BACKEND (Data Import & Migration)

## Data Analysis

### Source: javi_content.json
- **Records:** 25,403
- **c0id range:** 1 - 26,587
- **Fields:** c0id, c1word, c2phonetic, c3short_mean, c4mean, c5opposite_word, c6synsets, c7related_words, c8han, c9grid, c10level

### Target: BookSetUnitDetail
- **word_id range:** 35 - 26,587
- **Unique word_ids:** 15,006

### Mapping

| javi_content.json | → | Word Model |
|-------------------|---|------------|
| `c0id` | → | Sẽ dùng để map, KHÔNG phải `id` |
| `c1word` | → | `j_word` |
| `c2phonetic` | → | `phonetic` |
| `c3short_mean` | → | `short_mean` |
| `c4mean` | → | `mean` |
| `c5opposite_word` | → | `opposite_word` |
| `c6synsets` | → | `synsets` |
| `c7related_words` | → | `related_words` |
| `c8han` | → | `han` |
| `c9grid` | → | `grid` |
| `c10level` | → | `level` (convert: 1→N1, 2→N2, etc.) |

---

## Strategy

### Option A: Import với ID mapping table (Recommended)
1. Import từ javi_content.json vào Word table (Django sẽ tự assign ID mới)
2. Tạo mapping table: `c0id` → `new_word_id`
3. Update `UnitWordDetail.word_id` theo mapping

### Option B: Force ID (Risky)
- Import với `id = c0id` - có thể conflict với dữ liệu hiện tại

**Chọn Option A** vì an toàn hơn và không ảnh hưởng Word hiện tại.

---

## Proposed Changes

### Phase 1: Import Javi Content

#### [NEW] [import_javi_content.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/vocabulary/management/commands/import_javi_content.py)

```python
# 1. Load javi_content.json
# 2. For each record:
#    - Create Word object
#    - Store mapping: c0id → new_word.id
# 3. Save mapping to JSON file for Phase 2
```

**Output:**
- ~25,403 new Word records
- `c0id_to_word_id_mapping.json` file

---

### Phase 2: Remap UnitWordDetail

#### [NEW] [remap_bookset_words.py](file:///Users/macbook/Documents/Workspace/startjlpt_be/apps/learning/management/commands/remap_bookset_words.py)

```python
# 1. Load mapping from Phase 1
# 2. Update UnitWordDetail records:
#    - Old word_id (c0id) → New word_id
# 3. Update migrated BookSet lessons only
```

---

## Task Breakdown

### Phase 1: Import Javi Content
| Task | Priority | Est. Time |
|------|----------|-----------|
| 1.1 Create import command | P0 | 15 min |
| 1.2 Handle level conversion (1→N1) | P0 | 5 min |
| 1.3 Handle JSON fields (mean, synsets) | P0 | 5 min |
| 1.4 Generate mapping file | P0 | 5 min |
| 1.5 Run import | P0 | 5 min |

### Phase 2: Remap UnitWordDetail
| Task | Priority | Est. Time |
|------|----------|-----------|
| 2.1 Create remap command | P0 | 10 min |
| 2.2 Update UnitWordDetail records | P0 | 5 min |
| 2.3 Verify remapping | P0 | 5 min |

---

## Phase X: Verification

### Automated Tests
```bash
# After Phase 1 - Check Word count increased
docker compose exec web python manage.py shell -c "
from apps.vocabulary.models import Word
print(f'Total Words: {Word.objects.count()}')
"

# After Phase 2 - Test unit detail API
curl "http://localhost:8000/api/learning/units/1807/detail/"
# Should return items from javi_content
```

### Manual Verification
1. Check MimiKara N1 - Bài 1 returns 100 words
2. Check word content matches javi_content.json

---

## Estimated Time

| Phase | Time |
|-------|------|
| Phase 1: Import | 35 min |
| Phase 2: Remap | 20 min |
| Phase X: Verification | 10 min |
| **TOTAL** | **~65 min** |

---

## Rollback Strategy

```python
# If needed, delete imported words (those not in original Word table)
# Mapping file will contain which words were imported
```
