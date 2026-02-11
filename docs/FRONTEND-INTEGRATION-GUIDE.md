# JLPT Start Backend - Frontend Integration Guide

> Tài liệu chi tiết cho Frontend Developer tích hợp với Backend API.

---

## 📌 Mục lục

1. [Thông tin chung](#1-thông-tin-chung)
2. [Authentication](#2-authentication)
3. [API Endpoints](#3-api-endpoints)
4. [Data Models](#4-data-models)
5. [Error Handling](#5-error-handling)
6. [Best Practices](#6-best-practices)

---

## 1. Thông tin chung

### Base URL

| Environment | URL |
|-------------|-----|
| **Local** | `http://localhost:8000/api/` |
| **Production** | `https://api.jlptstart.com/api/` |

### API Documentation (Interactive)

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### Response Format

Tất cả app APIs đều trả về dạng chuẩn:

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

Giá trị của `meta.type`:
- `SUCCESS`: status code < 400
- `ERROR`: status code >= 400

Lưu ý: để tài liệu gọn, nhiều ví dụ ở các section sau có thể chỉ mô tả phần payload bên trong `data`.

### Timestamps

- Tất cả timestamps đều ở UTC timezone
- Format: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)

---

## 2. Authentication

### 🔐 Quy tắc bắt buộc

> **Tất cả API endpoints (trừ auth) đều yêu cầu JWT token trong header.**

```http
Authorization: Bearer <access_token>
```

### 2.1. Đăng ký (Registration)

**Flow đăng ký:**
1. User đăng ký → Nhận OTP qua email
2. User verify OTP → Tài khoản được kích hoạt
3. User login → Nhận JWT tokens

#### POST `/api/auth/registration/`

**Request:**
```json
{
  "email": "user@example.com",
  "password1": "SecurePass123!",
  "password2": "SecurePass123!",
  "display_name": "Nguyen Van A"  // optional
}
```

**Response (201 Created):**
```json
{
  "meta": {
    "code": 201,
    "type": "SUCCESS",
    "message": "Verification Code has been sent to your email."
  },
  "data": {
    "email": "user@example.com"
  }
}
```

> ⚠️ **Username không được sử dụng.** Dự án dùng email làm identifier duy nhất.

---

### 2.2. Xác thực OTP

#### POST `/api/users/verify-otp/`

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Account verified successfully"
  },
  "data": {}
}
```

**Error (400 Bad Request):**
```json
{
  "meta": {
    "code": 400,
    "type": "ERROR",
    "message": "Invalid or expired OTP"
  },
  "data": {}
}
```

#### POST `/api/users/resend-otp/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

---

### 2.3. Đăng nhập (Login)

#### POST `/api/auth/login/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {
    "access": {
      "token": "eyJ0eXAiOiJKV1QiLC...",
      "expires_at": "2024-01-01T01:00:00Z"
    },
    "refresh": {
      "token": "eyJ0eXAiOiJKV1QiLC...",
      "expires_at": "2024-01-08T00:00:00Z"
    },
    "user": {
      "id": 1,
      "email": "user@example.com",
      "display_name": "Nguyen Van A",
      "avatar": null,
      "role": "USER",
      "level": "N5",
      "streak": 0
    }
  }
}
```

---

### 2.4. Refresh Token

#### POST `/api/auth/token/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLC..."
}
```

**Response (200 OK):**
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {
    "access": {
      "token": "eyJ0eXAiOiJKV1QiLC...",
      "expires_at": "2024-01-01T02:00:00Z"
    },
    "refresh": {
      "token": "eyJ0eXAiOiJKV1QiLC...",
      "expires_at": "2024-01-08T01:00:00Z"
    }
  }
}
```

---

### 2.5. Logout

#### POST `/api/auth/logout/`

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Successfully logged out."
  },
  "data": {}
}
```

---

### 2.6. Password Reset

#### POST `/api/auth/password/reset/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

---

## 3. API Endpoints

### 3.1. User Profile

#### GET `/api/users/profile/`

Lấy thông tin user hiện tại.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "display_name": "Nguyen Van A",
  "avatar": "https://example.com/avatar.jpg",
  "first_name": "A",
  "last_name": "Nguyen Van",
  "role": "USER",
  "login_method": "EMAIL",
  "status": "ACTIVE",
  "level": "N5",
  "streak": 15,
  "last_study_date": "2024-01-01",
  "date_joined": "2023-12-01T00:00:00Z"
}
```

#### PUT/PATCH `/api/users/profile/`

Cập nhật thông tin user.

**Request (PATCH):**
```json
{
  "display_name": "New Name",
  "level": "N4"
}
```

**Editable fields:**
- `display_name`
- `avatar`
- `first_name`
- `last_name`
- `level`

---

### 3.2. User Stats

#### GET `/api/users/stats/`

**Response:**
```json
{
  "streak": 15,
  "level": "N5",
  "last_study_date": "2024-01-01"
}
```

---

### 3.3. Vocabulary

#### GET `/api/vocabulary/`

List từ vựng.

**Query Params:**
- `?level=N5` - Filter theo JLPT level
- `?search=食べる` - Tìm kiếm
- `?ordering=j_word` - Sắp xếp

---

#### GET `/api/vocabulary/{id}/`

Chi tiết 1 từ.

---

#### GET `/api/vocabulary/by_level/?level=N5`

Lấy từ vựng theo level.

---

### 3.4. Kanji

#### GET `/api/kanjis/`

List kanji.

**Query Params:**
- `?level=N5`
- `?search=日`
- `?ordering=stroke_count`

---

#### GET `/api/kanjis/{id}/`

Chi tiết kanji.

---

#### GET `/api/kanjis/by_level/?level=N5`

Lấy kanji theo level.

---

### 3.5. Grammar

#### GET `/api/grammar/`

List ngữ pháp.

**Query Params:**
- `?level=N5`
- `?search=は`
- `?ordering=title`

---

#### GET `/api/grammar/{id}/`

Chi tiết ngữ pháp.

---

#### GET `/api/grammar/by_level/?level=N5`

Lấy ngữ pháp theo level.

---

### 3.6. Examples

#### GET `/api/examples/`

List ví dụ.

#### GET `/api/examples/{id}/`

Chi tiết ví dụ.

**Response:**
```json
{
  "id": 18909,
  "content": "私あてに電話してください。",
  "mean": "Làm ơn gọi điện cho tôi.",
  "trans": "わたしあてにでんわしてください。",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### 3.7. Learning Module

#### GET `/api/learning/lessons/`

List tất cả lessons.

**Query Params:**
- `?level=N5` - Filter theo JLPT level
- `?search=beginner` - Tìm kiếm theo tên
- `?ordering=id` - Sắp xếp

**Response:**
```json
[
  {
    "id": 1,
    "lession_name": "Beginner Lessons",
    "level": "N6",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

---

#### GET `/api/learning/lessons/{id}/`

Chi tiết 1 lesson.

---

#### GET `/api/learning/lessons/{id}/units/`

Lấy tất cả units của 1 lesson.

**Query Params:**
- `?unit_type=vocabulary` - Filter theo loại (vocabulary, grammar, kanji)

**Response:**
```json
{
  "lesson": {
    "id": 1,
    "lession_name": "Beginner Lessons",
    "level": "N6"
  },
  "summary": {
    "total_units": 10,
    "vocabulary_units": 5,
    "grammar_units": 3,
    "kanji_units": 2
  },
  "units": [
    {
      "id": 1,
      "unit_name": "1. はじめまして",
      "lession_id": "1",
      "total": "60",
      "unit_type": "vocabulary",
      "level": null
    }
  ]
}
```

---

#### GET `/api/learning/units/`

List tất cả units.

**Query Params:**
- `?lession_id=1` - Filter theo lesson
- `?unit_type=vocabulary` - Filter theo loại
- `?level=N5` - Filter theo level

---

#### GET `/api/learning/units/{id}/detail/`

⭐ **API quan trọng nhất** - Lấy chi tiết unit với đầy đủ nội dung.

**Response (unit_type="vocabulary"):**
```json
{
  "unit": {
    "id": 1,
    "unit_name": "1. はじめまして",
    "lession_id": "1",
    "total": "60",
    "unit_type": "vocabulary",
    "level": null
  },
  "items": [
    {
      "id": 9870,
      "j_word": "私",
      "phonetic": "わたし",
      "short_mean": "tôi",
      "han": null,
      "grid": null,
      "level": "",
      "mean": [
        {
          "kind": "n, adj-no",
          "mean": "tôi",
          "examples": [18909]
        }
      ],
      "opposite_word": ["貴方", "公"],
      "synsets": null,
      "related_words": null,
      "meaning_count": 1,
      "is_advanced": false,
      "all_meanings": ["tôi"],
      "all_synonyms": [],
      "examples": [
        {
          "id": 18909,
          "content": "私あてに電話してください。",
          "mean": "Làm ơn gọi điện cho tôi.",
          "trans": "わたしあてにでんわしてください。"
        }
      ]
    }
  ]
}
```

**Response (unit_type="grammar"):**
```json
{
  "unit": { ... },
  "items": [
    {
      "id": 1,
      "title": "〜は〜です",
      "mean": "A là B",
      "level": "N5",
      "level_display": "N5",
      "note": "Cấu trúc cơ bản nhất",
      "structure": "A は B です",
      "about": "Dùng để giới thiệu...",
      "fun_fact": null,
      "caution": null,
      "examples": [...],
      "synonyms": null,
      "example_count": 3
    }
  ]
}
```

**Response (unit_type="kanji"):**
```json
{
  "unit": { ... },
  "items": [
    {
      "id": 1,
      "kanji": "日",
      "mean": "ngày, mặt trời",
      "level": "N5",
      "level_display": "N5",
      "on": "ニチ、ジツ",
      "kun": "ひ、-び、-か",
      "img": null,
      "detail": "...",
      "freq": 1,
      "comp": null,
      "stroke_count": 4,
      "compDetail": null,
      "examples": [...],
      "example_count": 5
    }
  ]
}
```

---

#### User Progress

##### GET `/api/learning/progress/`

List progress của user.

**Query Params:**
- `?user_id=1`
- `?unit_id=1`
- `?lession_id=1`

##### POST `/api/learning/progress/`

Tạo/cập nhật progress.

**Request:**
```json
{
  "unit_id": "1",
  "lession_id": "1",
  "user_id": "1",
  "progress": 50
}
```

---

#### Anki Learning Theo Unit

Các API này dùng scheduler kiểu Anki (SM-2 style): `again`, `hard`, `good`, `easy`.
Chi tiết đầy đủ thuật toán và state machine: `docs/api/anki-unit-learning.md`.

##### GET `/api/learning/units/{id}/anki/next/`

Lấy card tiếp theo cần học trong unit cho user hiện tại.

**Query Params:**
- `?include_future=true` - nếu không có card đến hạn thì trả card gần nhất trong tương lai.

**Response:**
```json
{
  "unit": {
    "id": 1,
    "unit_name": "Unit 1",
    "unit_type": "vocabulary"
  },
  "sync": {
    "total_items": 50,
    "created_cards": 50
  },
  "card": {
    "card_id": 1201,
    "unit_id": "1",
    "item_type": "vocabulary",
    "item_id": "11192",
    "state": "new",
    "step_index": 0,
    "interval_days": 0,
    "ease_factor": 2.5,
    "reps": 0,
    "lapses": 0,
    "due_at": "2026-02-11T16:40:00Z",
    "last_reviewed_at": null,
    "content": { "...": "word/grammar/kanji payload" }
  },
  "card_is_due": true,
  "stats": {
    "total_cards": 50,
    "due_now": 50,
    "new_cards": 50,
    "learning_cards": 0,
    "relearning_cards": 0,
    "review_cards": 0,
    "next_due_at": null
  }
}
```

##### POST `/api/learning/units/{id}/anki/review/`

Gửi kết quả trả lời cho 1 card.

**Request:**
```json
{
  "card_id": 1201,
  "rating": "good",
  "response_time_ms": 2400
}
```

`rating` chỉ nhận: `again`, `hard`, `good`, `easy`.

**Response:**
```json
{
  "unit": { "...": "unit payload" },
  "reviewed_card": { "...": "updated card state" },
  "next_card": { "...": "next card payload" },
  "next_card_is_due": true,
  "stats": {
    "total_cards": 50,
    "due_now": 49,
    "new_cards": 49,
    "learning_cards": 1,
    "relearning_cards": 0,
    "review_cards": 0,
    "next_due_at": "2026-02-11T16:41:00Z"
  }
}
```

##### GET `/api/learning/units/{id}/anki/stats/`

Lấy thống kê hàng đợi học Anki của unit.

---

## 4. Data Models

### 4.1. User

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | ID |
| `email` | string | Email (unique) |
| `display_name` | string | Tên hiển thị |
| `avatar` | string/null | URL avatar |
| `first_name` | string | Họ |
| `last_name` | string | Tên |
| `role` | enum | `USER`, `ADMIN` |
| `login_method` | enum | `EMAIL`, `GOOGLE`, `FACEBOOK` |
| `status` | enum | `ACTIVE`, `INACTIVE`, `BANNED` |
| `level` | enum | `N6`, `N5`, `N4`, `N3`, `N2`, `N1` |
| `streak` | int | Số ngày học liên tiếp |
| `last_study_date` | date/null | Ngày học gần nhất |
| `date_joined` | datetime | Ngày đăng ký |

---

### 4.2. JLPT Levels

| Level | Description |
|-------|-------------|
| `N6` | Beginner (custom) |
| `N5` | Basic |
| `N4` | Elementary |
| `N3` | Intermediate |
| `N2` | Pre-Advanced |
| `N1` | Advanced |

---

### 4.3. Unit Types

| Type | Description |
|------|-------------|
| `vocabulary` | Vocabulary unit |
| `grammar` | Grammar unit |
| `kanji` | Kanji unit |

---

### 4.4. Word (Vocabulary)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | ID |
| `j_word` | string | Từ tiếng Nhật |
| `phonetic` | string | Phiên âm (hiragana/katakana) |
| `short_mean` | string | Nghĩa ngắn gọn |
| `han` | string/null | Hán tự |
| `grid` | int/null | Grid level |
| `level` | string | JLPT level (N1-N5) |
| `mean` | array | Chi tiết nghĩa [{kind, mean, examples}] |
| `opposite_word` | array/null | Từ trái nghĩa |
| `synsets` | array/null | Synonyms |
| `related_words` | array/null | Từ liên quan |
| `meaning_count` | int | Số lượng nghĩa |
| `is_advanced` | bool | Là từ nâng cao |
| `all_meanings` | array | Tất cả nghĩa (flattened) |
| `all_synonyms` | array | Tất cả từ đồng nghĩa |
| `examples` | array | Ví dụ [{id, content, mean, trans}] |

---

### 4.5. Grammar

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | ID |
| `title` | string | Tiêu đề ngữ pháp |
| `mean` | string | Nghĩa |
| `level` | string | JLPT level |
| `level_display` | string | JLPT level hiển thị |
| `note` | string/null | Ghi chú |
| `structure` | string | Cấu trúc |
| `about` | string/null | Giải thích |
| `fun_fact` | string/null | Fun fact |
| `caution` | string/null | Lưu ý |
| `examples` | array | Ví dụ |
| `synonyms` | array/null | Ngữ pháp tương tự |
| `example_count` | int | Số lượng ví dụ |

---

### 4.6. Kanji

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | ID |
| `kanji` | string | Chữ Kanji |
| `mean` | string | Nghĩa |
| `level` | string | JLPT level |
| `level_display` | string | JLPT level hiển thị |
| `on` | string | Âm on (onyomi) |
| `kun` | string | Âm kun (kunyomi) |
| `img` | string/null | Hình ảnh |
| `detail` | string/null | Chi tiết |
| `freq` | int/null | Tần suất sử dụng |
| `comp` | string/null | Thành phần |
| `stroke_count` | int/null | Số nét |
| `compDetail` | string/null | Chi tiết thành phần |
| `examples` | array | Ví dụ |
| `example_count` | int | Số lượng ví dụ |

---

## 5. Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (no permission) |
| `404` | Not Found |
| `500` | Server Error |

### Error Response Format

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

### Token Expired

Khi token hết hạn, response:

```json
{
  "meta": {
    "code": 401,
    "type": "ERROR",
    "message": "Token is invalid"
  },
  "data": {}
}
```

**→ Frontend nên tự động refresh token hoặc redirect về login.**

---

## 6. Best Practices

### 6.1. Token Management

```javascript
// Lưu tokens sau login
localStorage.setItem('accessToken', response.data.data.access.token);
localStorage.setItem('refreshToken', response.data.data.refresh.token);
localStorage.setItem('tokenExpiry', response.data.data.access.expires_at);

// Axios interceptor để tự động thêm token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto refresh khi token sắp hết hạn
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        const newTokens = await refreshAccessToken(refreshToken);
        // Retry original request với token mới
      }
    }
    return Promise.reject(error);
  }
);
```

### 6.2. Pagination

Một số endpoints hỗ trợ pagination:

```
GET /api/vocabulary/?page=1&page_size=20
```

Response:
```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {
    "count": 1000,
    "next": "http://api.example.com/api/vocabulary/?page=2",
    "previous": null,
    "results": [...]
  }
}
```

### 6.3. Caching

Recommend cache các data ít thay đổi:
- Vocabulary list (cache 1 hour)
- Grammar list (cache 1 hour)
- Kanji list (cache 1 hour)
- User profile (cache 5 minutes)

### 6.4. Offline Support

Recommend lưu xuống local storage:
- Unit content đang học
- User progress
- Favorites/bookmarks

---

## 📞 Support

- **Swagger Docs**: `/api/docs/`
- **GitHub**: https://github.com/dabi61/jlpt-start-be
