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

## 3. Vocabulary APIs
- `GET/POST /api/vocabulary/`
- `GET/PUT/PATCH/DELETE /api/vocabulary/{id}/`
- `GET /api/vocabulary/by_level/?level=N5`
- `GET /api/vocabulary/stats/`
- `GET /api/vocabulary/{id}/examples/`

## 4. Kanji APIs
- `GET/POST /api/kanjis/`
- `GET/PUT/PATCH/DELETE /api/kanjis/{id}/`
- `GET /api/kanjis/stats/`
- `GET /api/kanjis/{id}/examples/`
- `GET /api/kanjis/{id}/components/`

## 5. Grammar APIs
- `GET/POST /api/grammar/`
- `GET/PUT/PATCH/DELETE /api/grammar/{id}/`
- `GET /api/grammar/stats/`
- `GET /api/grammar/{id}/examples/`
- `GET /api/grammar/{id}/synonyms/`

## 6. Example APIs
- `GET/POST /api/examples/`
- `GET/PUT/PATCH/DELETE /api/examples/{id}/`

Pagination:
- List endpoints and custom list actions support `page` and `page_size`.
- Examples:
  - `GET /api/examples/?page=1&page_size=20`
  - `GET /api/grammar/{id}/examples/?page=1&page_size=10`
  - `GET /api/kanjis/{id}/examples/?page=2&page_size=10`

## 7. Remaining APIs
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

## 8. API Metadata
- `GET /api/schema/`: OpenAPI schema.
- `GET /api/docs/`: Swagger UI.
- `GET /api/redoc/`: ReDoc.

## 9. Response Envelope
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
