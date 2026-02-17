# API Endpoints (Current)

## 1. Authentication
- `POST /api/auth/registration/`: Register account (returns OTP flow message).
- `POST /api/auth/login/`: Login with email/password.
- `POST /api/auth/token/refresh/`: Refresh access token.
- `POST /api/users/verify-otp/`: Verify OTP and activate account.
- `POST /api/users/resend-otp/`: Resend OTP.
- `POST /api/auth/logout/`: Logout.
- `POST /api/auth/password/change/`: Change password.
- `POST /api/auth/password/reset/`: Request password reset email.
- `POST /api/auth/password/reset/confirm/<uidb64>/<token>/`: Confirm reset.
- `GET /api/auth/user/`: Get current auth user details.

## 2. User APIs
- `GET /api/users/profile/`: Get profile.
- `PUT/PATCH /api/users/profile/`: Update profile.
- `GET /api/users/stats/`: Get user learning stats (`level`, `streak`, `last_study_date`).
- `POST /api/users/avatar/upload-url/`: Get presigned upload URL for avatar (Cloudflare R2).
- `POST /api/users/avatar/confirm/`: Confirm uploaded image and set avatar.
- `PUT/POST /api/users/avatar/`: Upload avatar (raw bytes or multipart) and set avatar (backend uploads to R2).
- `DELETE /api/users/avatar/`: Delete current avatar.
- Avatar integration guide: `docs/api/avatar-cloudflare.md`.

## 3. Practice Attempts (per-user answers)
- `GET/POST /api/practice/attempts/`
- `GET /api/practice/attempts/{id}/`
- `GET/POST /api/practice/attempts/{id}/answers/`
- `POST /api/practice/attempts/{id}/submit/`
- `POST /api/practice/attempts/{id}/abandon/`
- `GET /api/practice/attempts/progress/`
- Attempts/answers guide: `docs/api/practice.md`

## 4. Vocabulary APIs
- `GET/POST /api/vocabulary/`
- `GET/PUT/PATCH/DELETE /api/vocabulary/{id}/`
- `GET /api/vocabulary/by_level/?level=N5`
- `GET /api/vocabulary/stats/`
- `GET /api/vocabulary/{id}/examples/`

## 5. Kanji APIs
- `GET/POST /api/kanjis/`
- `GET/PUT/PATCH/DELETE /api/kanjis/{id}/`
- `GET /api/kanjis/stats/`
- `GET /api/kanjis/{id}/examples/`
- `GET /api/kanjis/{id}/components/`

## 6. Grammar APIs
- `GET/POST /api/grammar/`
- `GET/PUT/PATCH/DELETE /api/grammar/{id}/`
- `GET /api/grammar/stats/`
- `GET /api/grammar/{id}/examples/`
- `GET /api/grammar/{id}/synonyms/`

## 7. Example APIs
- `GET/POST /api/examples/`
- `GET/PUT/PATCH/DELETE /api/examples/{id}/`

Pagination:
- List endpoints and custom list actions support `page` and `page_size`.
- Examples:
  - `GET /api/examples/?page=1&page_size=20`
  - `GET /api/grammar/{id}/examples/?page=1&page_size=10`
  - `GET /api/kanjis/{id}/examples/?page=2&page_size=10`

## 8. Remaining APIs
### Learning
- `GET/POST /api/learning/lessons/`
- `GET/PUT/PATCH/DELETE /api/learning/lessons/{id}/`
- `GET /api/learning/lessons/{id}/units/`: Units of one lesson (+summary).

- `GET/POST /api/learning/units/`
- `GET/PUT/PATCH/DELETE /api/learning/units/{id}/`
- `GET /api/learning/units/{id}/detail/`: Resolve full unit content.
- `GET /api/learning/units/{id}/anki/next/`: Get next Anki card in this unit for current user.
- `POST /api/learning/units/{id}/anki/review/`: Submit `again|hard|good|easy` for one Anki card.
- `GET /api/learning/units/{id}/anki/stats/`: Get Anki queue stats for this unit.

- `GET/POST /api/learning/progress/`
- `GET/PUT/PATCH/DELETE /api/learning/progress/{id}/`

Learning pagination:
- `page` (default: `1`)
- `page_size` (max `100`)
- `GET /api/learning/lessons/{id}/units/?page=1&page_size=20`
- `GET /api/learning/units/{id}/detail/?page=1&page_size=20`

Anki learning flow (per unit):
- First call `GET /anki/next/` to initialize/sync cards and fetch one card.
- Submit answer with `POST /anki/review/` (`rating`: `again`, `hard`, `good`, `easy`).
- Read queue status from `GET /anki/stats/`.
- Scheduler uses Anki-style SM-2 concepts: ease factor, intervals, learning/relearning/review states.
- Detailed integration/spec: `docs/api/anki-unit-learning.md`.

### Courses
- `GET /api/courses/`

### N2 Practice
- `GET/POST /api/n2/sections/`
- `GET/PUT/PATCH/DELETE /api/n2/sections/{id}/`
- `GET/POST /api/n2/subcategories/`
- `GET/PUT/PATCH/DELETE /api/n2/subcategories/{id}/`
- `GET/POST /api/n2/exams/`
- `GET/PUT/PATCH/DELETE /api/n2/exams/{id}/`
- `GET /api/n2/exams/{id}/questions/`
- `GET/POST /api/n2/questions/`
- `GET/PUT/PATCH/DELETE /api/n2/questions/{id}/`
- `GET /api/n2/questions/{id}/items/`
- `GET/POST /api/n2/question-items/`
- `GET/PUT/PATCH/DELETE /api/n2/question-items/{id}/`
- `GET/POST /api/n2/media-assets/`
- `GET/PUT/PATCH/DELETE /api/n2/media-assets/{id}/`
- Import command + mapping guide: `docs/api/n2.md`

### N3 Practice
- `GET/POST /api/n3/sections/`
- `GET/PUT/PATCH/DELETE /api/n3/sections/{id}/`
- `GET/POST /api/n3/subcategories/`
- `GET/PUT/PATCH/DELETE /api/n3/subcategories/{id}/`
- `GET/POST /api/n3/exams/`
- `GET/PUT/PATCH/DELETE /api/n3/exams/{id}/`
- `GET /api/n3/exams/{id}/questions/`
- `GET/POST /api/n3/questions/`
- `GET/PUT/PATCH/DELETE /api/n3/questions/{id}/`
- `GET /api/n3/questions/{id}/items/`
- `GET/POST /api/n3/question-items/`
- `GET/PUT/PATCH/DELETE /api/n3/question-items/{id}/`
- `GET/POST /api/n3/media-assets/`
- `GET/PUT/PATCH/DELETE /api/n3/media-assets/{id}/`
- Import command + mapping guide: `docs/api/n3.md`

### N4 Practice
- `GET/POST /api/n4/sections/`
- `GET/PUT/PATCH/DELETE /api/n4/sections/{id}/`
- `GET/POST /api/n4/subcategories/`
- `GET/PUT/PATCH/DELETE /api/n4/subcategories/{id}/`
- `GET/POST /api/n4/exams/`
- `GET/PUT/PATCH/DELETE /api/n4/exams/{id}/`
- `GET /api/n4/exams/{id}/questions/`
- `GET/POST /api/n4/questions/`
- `GET/PUT/PATCH/DELETE /api/n4/questions/{id}/`
- `GET /api/n4/questions/{id}/items/`
- `GET/POST /api/n4/question-items/`
- `GET/PUT/PATCH/DELETE /api/n4/question-items/{id}/`
- `GET/POST /api/n4/media-assets/`
- `GET/PUT/PATCH/DELETE /api/n4/media-assets/{id}/`
- Import command + mapping guide: `docs/api/n4.md`

### N5 Practice
- `GET/POST /api/n5/sections/`
- `GET/PUT/PATCH/DELETE /api/n5/sections/{id}/`
- `GET/POST /api/n5/subcategories/`
- `GET/PUT/PATCH/DELETE /api/n5/subcategories/{id}/`
- `GET/POST /api/n5/exams/`
- `GET/PUT/PATCH/DELETE /api/n5/exams/{id}/`
- `GET /api/n5/exams/{id}/questions/`
- `GET/POST /api/n5/questions/`
- `GET/PUT/PATCH/DELETE /api/n5/questions/{id}/`
- `GET /api/n5/questions/{id}/items/`
- `GET/POST /api/n5/question-items/`
- `GET/PUT/PATCH/DELETE /api/n5/question-items/{id}/`
- `GET/POST /api/n5/media-assets/`
- `GET/PUT/PATCH/DELETE /api/n5/media-assets/{id}/`
- Import command + mapping guide: `docs/api/n5.md`

## 9. API Metadata
- `GET /api/schema/`: OpenAPI schema.
- `GET /api/docs/`: Swagger UI.
- `GET /api/redoc/`: ReDoc.

## 10. Response Envelope
- All app APIs return the same envelope shape.
- Note: `/api/schema/` keeps raw OpenAPI payload for Swagger/ReDoc compatibility.
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {}
}
```

- Error response example:
```json
{
  "meta": {
    "code": 401,
    "type": "ERROR",
    "message": "Missing or invalid authorization header."
  },
  "data": {}
}
```
