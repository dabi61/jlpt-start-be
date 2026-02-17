# Practice Attempts API (per-user answers)

Tài liệu này mô tả cách lưu đáp án theo **từng user** (không lưu vào dataset `N3/N4/N5QuestionItem.choose_answer` vì field đó mang tính “global”).

Base path: `/api/practice/`

## 1. Authentication (bắt buộc)

Tất cả endpoint đều yêu cầu đăng nhập (JWT Bearer).

```bash
Authorization: Bearer <ACCESS_TOKEN>
```

## 2. Khái niệm

### 2.1 Attempt

`PracticeAttempt` = 1 lần làm bài của 1 user cho 1 exam (theo level N*).

Fields chính:
- `level`: `N1..N6`
- `exam_id`: id của exam trong dataset (ví dụ `N3Exam.id`)
- `status`: `IN_PROGRESS | SUBMITTED | ABANDONED`
- `total_items`, `answered_items`, `correct_items`, `score`, `duration_ms`

### 2.2 Answer

`PracticeAnswer` = đáp án của user cho 1 question item trong 1 attempt.

Fields chính:
- `attempt`
- `question_item_id`: id của question item trong dataset (ví dụ `N3QuestionItem.id`)
- `selected_answer`
- `correct_answer`, `is_correct` (backend tự tính)
- `response_time_ms` (optional)

## 3. API endpoints

### 3.1 Start/Resume attempt

`POST /api/practice/attempts/`

Request:
```json
{
  "level": "N3",
  "exam_id": 15,
  "resume": true
}
```

Behavior:
- Nếu `resume=true` và user đã có attempt `IN_PROGRESS` cho đúng `(level, exam_id)` thì API sẽ trả lại attempt đó (`200`).
- Nếu chưa có thì tạo attempt mới (`201`).

### 3.2 List attempts (theo user hiện tại)

`GET /api/practice/attempts/?level=N3&exam_id=15&status=SUBMITTED&page=1&page_size=20`

Query params:
- `level` (optional)
- `exam_id` (optional)
- `status` (optional)

### 3.3 Save answer (single hoặc batch)

`POST /api/practice/attempts/{attempt_id}/answers/`

Single:
```json
{
  "question_item_id": 123,
  "selected_answer": 2,
  "response_time_ms": 4200
}
```

Batch:
```json
{
  "answers": [
    { "question_item_id": 123, "selected_answer": 2 },
    { "question_item_id": 124, "selected_answer": 1, "response_time_ms": 3200 }
  ]
}
```

Lưu ý:
- Backend sẽ validate `question_item_id` thuộc đúng exam của attempt.
- Backend tự set `correct_answer` + `is_correct`.

### 3.4 Get answers of an attempt

`GET /api/practice/attempts/{attempt_id}/answers/`

### 3.5 Submit attempt (chấm điểm + khóa attempt)

`POST /api/practice/attempts/{attempt_id}/submit/`

Backend sẽ:
- tính `total_items` từ dataset (`QuestionItem` count của exam)
- tính `answered_items`, `correct_items`, `score`
- set `status=SUBMITTED`, `submitted_at`

### 3.6 Abandon attempt

`POST /api/practice/attempts/{attempt_id}/abandon/`

### 3.7 Progress summary

`GET /api/practice/attempts/progress/`

Nếu thêm `level`:
`GET /api/practice/attempts/progress/?level=N3`

Trả về aggregate theo level hoặc theo exam (để bạn hiển thị tiến độ).

## 4. Client flow gợi ý

1. Lấy danh sách exam từ dataset:
   - ví dụ: `GET /api/n3/exams/?subcategory=...`
2. Start attempt:
   - `POST /api/practice/attempts/` với `level=N3` + `exam_id`
3. Load questions:
   - `GET /api/n3/exams/{exam_id}/questions/?page=1&page_size=20`
4. User chọn đáp án:
   - `POST /api/practice/attempts/{attempt_id}/answers/`
5. Nộp bài:
   - `POST /api/practice/attempts/{attempt_id}/submit/`

