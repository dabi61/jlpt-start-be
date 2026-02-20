# JLPT Start API - Mobile Kotlin Multiplatform Integration Guide

Tài liệu này dành cho team mobile (Kotlin Multiplatform) tích hợp trực tiếp với backend hiện tại.
Nội dung bám sát code và response runtime trong dự án.

- Cập nhật: 2026-02-20
- Base production: `https://jlpt.codes/api/`
- Base local: `http://localhost:8000/api/`

## 1. Tổng quan kỹ thuật

### 1.1 Quy ước URL
- Hầu hết endpoint dùng DRF Router, có trailing slash (`/`) ở cuối.
- Nên luôn gọi đúng dạng có `/` để tránh redirect không cần thiết.

Ví dụ đúng:
- `GET /api/users/profile/`
- `GET /api/learning/units/1/detail/`

### 1.2 Auth bắt buộc
Trừ các endpoint auth public, tất cả endpoint yêu cầu JWT access token:

```http
Authorization: Bearer <access_token>
```

### 1.3 Response envelope chuẩn
Tất cả app APIs trả về envelope:

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

- `meta.type = SUCCESS` khi status < 400
- `meta.type = ERROR` khi status >= 400

### 1.4 Pagination chuẩn
Các list endpoint dùng `PageNumberPagination`:
- Query params: `page`, `page_size`
- `page_size` max = `100`

Response phần `data`:

```json
{
  "count": 49089,
  "next": "http://localhost/api/vocabulary/?page=2&page_size=2",
  "previous": null,
  "results": []
}
```

### 1.5 Time format
- Hầu hết datetime: ISO-8601 UTC (`2026-02-20T04:51:17.728503Z`)
- Riêng JWT `expires_at` trong login/refresh là Unix epoch seconds (`Long`)

## 2. Authentication Flow (mobile)

## 2.1 Đăng ký
`POST /api/auth/registration/`

Request:

```json
{
  "email": "user@example.com",
  "password1": "StrongPass123!",
  "password2": "StrongPass123!",
  "display_name": "Nguyen Van A"
}
```

Response `201`:

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

Lưu ý:
- User được tạo ở trạng thái `INACTIVE`.
- Phải verify OTP trước khi login.

## 2.2 Verify OTP
`POST /api/users/verify-otp/`

Request:

```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

Response `200`:

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

OTP hiện tại hết hạn sau 5 phút.

## 2.3 Resend OTP
`POST /api/users/resend-otp/`

Request:

```json
{
  "email": "user@example.com"
}
```

Success message: `OTP sent successfully`.

## 2.4 Login
`POST /api/auth/login/`

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Response runtime mẫu `200`:

```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {
    "user": {
      "id": 32,
      "email": "kmp_doc_test@example.com",
      "display_name": "",
      "avatar": null,
      "avatar_image_id": null,
      "first_name": "",
      "last_name": "",
      "role": "USER",
      "login_method": "EMAIL",
      "status": "ACTIVE",
      "level": "N6",
      "streak": 0,
      "last_study_date": null,
      "date_joined": "2026-02-20T04:51:17.728503Z"
    },
    "access": {
      "token": "<jwt>",
      "expires_at": 1772167879
    },
    "refresh": {
      "token": "<jwt>",
      "expires_at": 1773291079
    }
  }
}
```

Lưu ý quan trọng:
- `expires_at` là **epoch seconds**, không phải ISO string.

## 2.5 Refresh Token
`POST /api/auth/token/refresh/`

Request:

```json
{
  "refresh": "<refresh_token>"
}
```

Response `200`:

```json
{
  "meta": {
    "code": 200,
    "type": "SUCCESS",
    "message": "Request successful."
  },
  "data": {
    "access": {
      "token": "<new_access>",
      "expires_at": 1772167896
    },
    "refresh": {
      "token": "<new_refresh>",
      "expires_at": 1773291096
    }
  }
}
```

## 2.6 Lấy user hiện tại
`GET /api/auth/user/`

Header: `Authorization: Bearer <access_token>`

Response `data` cùng shape với `user` trong login.

## 2.7 Password APIs
- `POST /api/auth/password/change/`
  - Body: `old_password`, `new_password1`, `new_password2`
- `POST /api/auth/password/reset/`
  - Body: `email`
- `POST /api/auth/password/reset/confirm/<uidb64>/<token>/`
  - Body theo chuẩn dj-rest-auth

## 2.8 Logout (thực tế mobile)
Endpoint `POST /api/auth/logout/` hiện trả `401` với message kiểu cookie-based (`Refresh token was not included in cookie data.`).

Khuyến nghị mobile hiện tại:
- Logout local bằng cách xóa token khỏi secure storage.
- Không phụ thuộc endpoint logout để revoke session.

## 3. User APIs

## 3.1 Profile
- `GET /api/users/profile/`
- `PUT/PATCH /api/users/profile/`

Editable fields:
- `display_name`
- `avatar`
- `first_name`
- `last_name`
- `level`

Patch response chỉ trả các field của serializer update.

## 3.2 Stats
`GET /api/users/stats/`

Response `data`:

```json
{
  "level": "N6",
  "streak": 1,
  "last_study_date": "2026-02-20",
  "display_name": "kmp_doc_test"
}
```

`display_name` ở đây có thể fallback từ email prefix nếu display_name rỗng.

## 3.3 Avatar

### Cách A: Presigned upload (khuyến nghị)
1. `POST /api/users/avatar/upload-url/`
2. Upload file trực tiếp tới `upload_url` bằng method `PUT`
3. `POST /api/users/avatar/confirm/` với `image_id`

### Cách B: Upload qua backend
- `PUT /api/users/avatar/` hoặc `POST /api/users/avatar/`
- Hỗ trợ:
  - `multipart/form-data` field `file` (hoặc `avatar`)
  - Raw bytes (`image/*` hoặc `application/octet-stream`)

### Xóa avatar
`DELETE /api/users/avatar/`

Chi tiết đầy đủ: `docs/api/avatar-cloudflare.md`.

## 4. Learning Module APIs

## 4.1 Lessons
- `GET /api/learning/lessons/`
- `GET /api/learning/lessons/{id}/`
- `GET /api/learning/lessons/{id}/units/`

Filters:
- lessons list: `level`, `search`, `ordering`
- lesson units action: `unit_type` (`vocabulary`, `grammar`, `kanji`)

`GET /lessons/{id}/units/` response có:
- `lesson`
- `summary`
- `count`, `next`, `previous` (khi paginate)
- `units`

## 4.2 Units
- `GET /api/learning/units/`
- `GET /api/learning/units/{id}/`
- `GET /api/learning/units/{id}/detail/`

Filters list units:
- `lession_id` (đúng chính tả API hiện tại, không phải `lesson_id`)
- `unit_type`
- `level`

`GET /units/{id}/detail/` trả:
- `unit`
- `page`, `page_size`, `count`, `next`, `previous`
- `items`

`items` sẽ map theo `unit_type`:
- vocabulary -> payload `WordSerializer`
- grammar -> payload `GrammarSerializer`
- kanji -> payload `KanjiSerializer`

## 4.3 Unit Anki APIs
- `GET /api/learning/units/{id}/anki/next/`
- `POST /api/learning/units/{id}/anki/review/`
- `GET /api/learning/units/{id}/anki/stats/`

`anki/review` request:

```json
{
  "card_id": 121,
  "rating": "good",
  "response_time_ms": 1500
}
```

`rating` hợp lệ: `again`, `hard`, `good`, `easy`.

Response chứa:
- `reviewed_card`
- `next_card`
- `next_card_is_due`
- `stats`

Chi tiết thuật toán scheduler: `docs/api/anki-unit-learning.md`.

## 4.4 Progress (upsert)
- `GET /api/learning/progress/`
- `POST /api/learning/progress/`
- `GET /api/learning/progress/{id}/`
- `PUT/PATCH/DELETE /api/learning/progress/{id}/`

`POST /progress/` là **upsert theo (user_id, unit_id)**:
- Lần đầu tạo -> `201`
- Đã có record -> update -> `200`

Request tối thiểu:

```json
{
  "unit_id": "1",
  "lession_id": "1",
  "progress": "40"
}
```

Lưu ý:
- User thường: backend bỏ qua `user_id` client gửi và dùng user từ JWT.
- Khi `progress >= 100`, backend set `completed_at` (nếu chưa có) và cập nhật streak.

## 5. Practice Attempts APIs (làm bài theo user)

Base: `/api/practice/attempts/`

Endpoints:
- `GET /api/practice/attempts/`
- `POST /api/practice/attempts/`
- `GET /api/practice/attempts/{id}/`
- `PUT/PATCH/DELETE /api/practice/attempts/{id}/`
- `GET/POST /api/practice/attempts/{id}/answers/`
- `POST /api/practice/attempts/{id}/submit/`
- `POST /api/practice/attempts/{id}/abandon/`
- `GET /api/practice/attempts/progress/`

## 5.1 Create/Resume attempt
Request:

```json
{
  "level": "N5",
  "exam_id": 15,
  "resume": true,
  "metadata": {}
}
```

Behavior:
- Nếu có attempt `IN_PROGRESS` cùng `(user, level, exam_id)` và `resume=true`: trả lại attempt cũ (`200`).
- Nếu không: tạo mới (`201`).

## 5.2 Save answers
Single:

```json
{
  "question_item_id": 123,
  "selected_answer": 2,
  "response_time_ms": 3200,
  "metadata": {}
}
```

Batch:

```json
{
  "answers": [
    { "question_item_id": 123, "selected_answer": 2 },
    { "question_item_id": 124, "selected_answer": 1 }
  ]
}
```

Rules:
- Backend validate `question_item_id` thuộc đúng exam của attempt.
- `correct_answer` và `is_correct` do backend tính.

## 5.3 Submit attempt
`POST /api/practice/attempts/{id}/submit/`

Backend set:
- `status=SUBMITTED`
- `total_items`, `answered_items`, `correct_items`, `score`, `duration_ms`, `submitted_at`

## 5.4 Progress summary
`GET /api/practice/attempts/progress/`

- Không có `level`: summary theo từng level.
- Có `level=N3`: summary theo từng exam trong level đó.

Chi tiết thêm: `docs/api/practice.md`.

## 6. JLPT Dataset APIs (N1-N5)

Các level `n1`, `n2`, `n3`, `n4`, `n5` có cùng cấu trúc endpoint, chỉ đổi prefix.

Ví dụ với `{level}`:
- Sections: `/api/{level}/sections/`
- Subcategories: `/api/{level}/subcategories/`
- Exams: `/api/{level}/exams/`
- Questions: `/api/{level}/questions/`
- Question items: `/api/{level}/question-items/`
- Media assets: `/api/{level}/media-assets/`

Custom actions:
- `GET /api/{level}/exams/{exam_id}/questions/`
- `GET /api/{level}/questions/{question_id}/items/`

## 6.1 Filters chính

Subcategories:
- `section`, `section_code`

Exams:
- `section`, `section_code`, `subcategory`, `subcategory_code`, `is_active`

Questions:
- `section`, `section_code`, `subcategory`, `subcategory_code`, `exam`, `kind`, `source_id`

Question items:
- `question`, `exam`, `subcategory`, `section`

Media assets:
- `media_type` (`IMAGE|AUDIO|OTHER`)
- `source_type` (`LOCAL|REMOTE`)

## 6.2 Nghiệp vụ quan trọng
Field `choose_answer` trong `question-items` là dữ liệu dataset (global), không nên dùng để lưu đáp án từng user.

Để lưu đáp án user theo session, luôn dùng Practice API (`/api/practice/attempts/...`).

## 7. Content APIs (Vocabulary/Grammar/Kanji/Examples)

## 7.1 Vocabulary
Base: `/api/vocabulary/`

Endpoints:
- `GET /api/vocabulary/`
- `GET /api/vocabulary/{id}/`
- `GET /api/vocabulary/by_level/?level=N5`
- `GET /api/vocabulary/stats/`
- `GET /api/vocabulary/{id}/examples/`

Write endpoints (`POST/PUT/PATCH/DELETE`) yêu cầu admin.

## 7.2 Grammar
Base: `/api/grammar/`

Endpoints:
- `GET /api/grammar/`
- `GET /api/grammar/{id}/`
- `GET /api/grammar/stats/`
- `GET /api/grammar/{id}/examples/`
- `GET /api/grammar/{id}/synonyms/`

Filter `level` kiểu **integer** (`1..5`), không phải `N1..N5`.

## 7.3 Kanji
Base: `/api/kanjis/`

Endpoints:
- `GET /api/kanjis/`
- `GET /api/kanjis/{id}/`
- `GET /api/kanjis/stats/`
- `GET /api/kanjis/{id}/examples/`
- `GET /api/kanjis/{id}/components/`

Filter `level` cũng là **integer** (`1..5`).

## 7.4 Examples
Base: `/api/examples/`

CRUD đầy đủ, đọc cho user authenticated, ghi cho admin.

## 7.5 Courses
`GET /api/courses/` hiện trả `501`:

```json
{
  "meta": {
    "code": 501,
    "type": "ERROR",
    "message": "Courses module is not implemented yet."
  },
  "data": {}
}
```

## 8. Permission matrix

## 8.1 Public (không cần JWT)
- `POST /api/auth/registration/`
- `POST /api/auth/login/`
- `POST /api/auth/token/refresh/`
- `POST /api/users/verify-otp/`
- `POST /api/users/resend-otp/`
- `POST /api/auth/password/reset/`
- `POST /api/auth/password/reset/confirm/<uidb64>/<token>/`

## 8.2 Authenticated user
- Hầu hết endpoint đọc dữ liệu học.
- Practice attempts của chính user.
- Learning progress (giới hạn theo user).
- User profile/avatar/stats.

## 8.3 Admin-only writes
Các module content/dataset (`vocabulary`, `grammar`, `kanjis`, `examples`, `n1..n5` datasets) dùng `IsAdminOrReadOnly`:
- User thường chỉ đọc.
- Ghi dữ liệu cần `is_staff` hoặc `is_superuser`.

## 9. KMP Network Architecture (khuyến nghị)

## 9.1 Dependencies (shared/commonMain)
Ví dụ với Ktor + kotlinx serialization + datetime:

```kotlin
dependencies {
    implementation("io.ktor:ktor-client-core:<version>")
    implementation("io.ktor:ktor-client-content-negotiation:<version>")
    implementation("io.ktor:ktor-serialization-kotlinx-json:<version>")
    implementation("io.ktor:ktor-client-auth:<version>")
    implementation("io.ktor:ktor-client-logging:<version>")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:<version>")
    implementation("org.jetbrains.kotlinx:kotlinx-datetime:<version>")
}
```

Thêm engine theo platform:
- Android: `ktor-client-okhttp`
- iOS: `ktor-client-darwin`

## 9.2 Envelope DTO

```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class ApiMeta(
    val code: Int,
    val type: String,
    val message: String
)

@Serializable
data class ApiEnvelope<T>(
    val meta: ApiMeta,
    val data: T? = null
)

@Serializable
data class PagedResult<T>(
    val count: Int,
    val next: String? = null,
    val previous: String? = null,
    val results: List<T>
)
```

## 9.3 Auth DTOs (đúng runtime)

```kotlin
@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class RegisterRequest(
    val email: String,
    val password1: String,
    val password2: String,
    val display_name: String? = null
)

@Serializable
data class VerifyOtpRequest(val email: String, val otp: String)

@Serializable
data class RefreshRequest(val refresh: String)

@Serializable
data class TokenPayload(
    val token: String,
    val expires_at: Long // epoch seconds
)

@Serializable
data class UserDto(
    val id: Long,
    val email: String,
    val display_name: String = "",
    val avatar: String? = null,
    val avatar_image_id: String? = null,
    val first_name: String = "",
    val last_name: String = "",
    val role: String,
    val login_method: String,
    val status: String,
    val level: String,
    val streak: Int,
    val last_study_date: String? = null,
    val date_joined: String
)

@Serializable
data class LoginData(
    val user: UserDto,
    val access: TokenPayload,
    val refresh: TokenPayload
)

@Serializable
data class RefreshData(
    val access: TokenPayload,
    val refresh: TokenPayload? = null
)
```

## 9.4 HttpClient + auth refresh

Lưu ý:
- Trong snippet này, `baseUrl` nên để dạng host gốc, ví dụ `https://jlpt.codes` (không thêm `/api`).
- Khi gọi API thì dùng path đầy đủ bắt đầu bằng `/api/...`.

```kotlin
class TokenStore {
    suspend fun getAccessToken(): String? = TODO()
    suspend fun getRefreshToken(): String? = TODO()
    suspend fun save(access: String, accessExp: Long, refresh: String, refreshExp: Long?) = TODO()
    suspend fun clear() = TODO()
}

class AuthApi(private val client: HttpClient) {
    suspend fun refresh(refreshToken: String): RefreshData {
        val response = client.post("/api/auth/token/refresh/") {
            contentType(ContentType.Application.Json)
            setBody(RefreshRequest(refreshToken))
            markAsRefreshTokenRequest()
        }
        val envelope = response.body<ApiEnvelope<RefreshData>>()
        if (envelope.meta.code >= 400 || envelope.data == null) {
            error(envelope.meta.message)
        }
        return envelope.data
    }
}
```

```kotlin
import io.ktor.client.*
import io.ktor.client.plugins.auth.*
import io.ktor.client.plugins.auth.providers.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.client.plugins.*
import io.ktor.http.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json

fun createHttpClient(
    baseUrl: String,
    tokenStore: TokenStore,
    authApi: AuthApi,
): HttpClient {
    val refreshMutex = Mutex()
    val apiHost = Url(baseUrl).host

    return HttpClient {
        install(ContentNegotiation) {
            json(
                Json {
                    ignoreUnknownKeys = true
                    explicitNulls = false
                }
            )
        }

        defaultRequest {
            url(baseUrl)
            contentType(ContentType.Application.Json)
            accept(ContentType.Application.Json)
        }

        install(Auth) {
            bearer {
                loadTokens {
                    val access = tokenStore.getAccessToken()
                    val refresh = tokenStore.getRefreshToken()
                    if (access != null && refresh != null) BearerTokens(access, refresh) else null
                }

                refreshTokens {
                    refreshMutex.withLock {
                        val currentRefresh = tokenStore.getRefreshToken() ?: return@withLock null
                        val refreshed = runCatching { authApi.refresh(currentRefresh) }.getOrNull()
                            ?: run {
                                tokenStore.clear()
                                return@withLock null
                            }

                        val newAccess = refreshed.access.token
                        val newRefresh = refreshed.refresh?.token ?: currentRefresh

                        tokenStore.save(
                            access = newAccess,
                            accessExp = refreshed.access.expires_at,
                            refresh = newRefresh,
                            refreshExp = refreshed.refresh?.expires_at
                        )

                        BearerTokens(newAccess, newRefresh)
                    }
                }

                sendWithoutRequest { request ->
                    request.url.host == apiHost
                }
            }
        }

        HttpResponseValidator {
            validateResponse { response ->
                if (!response.status.isSuccess()) {
                    // parse envelope để lấy message backend nếu cần
                }
            }
        }
    }
}
```

## 9.5 Safe call wrapper

```kotlin
sealed class ApiResult<out T> {
    data class Success<T>(val value: T, val message: String) : ApiResult<T>()
    data class Failure(val code: Int?, val message: String) : ApiResult<Nothing>()
}

suspend inline fun <reified T> HttpClient.getEnvelope(path: String): ApiResult<T> {
    return try {
        val envelope = get(path).body<ApiEnvelope<T>>()
        if (envelope.meta.code in 200..299 && envelope.data != null) {
            ApiResult.Success(envelope.data, envelope.meta.message)
        } else {
            ApiResult.Failure(envelope.meta.code, envelope.meta.message)
        }
    } catch (t: Throwable) {
        ApiResult.Failure(null, t.message ?: "Unknown network error")
    }
}
```

## 9.6 Mã lỗi nên map cho UI
- `400`: input/validation error
- `401`: cần login lại hoặc refresh fail
- `403`: không đủ quyền
- `404`: resource không tồn tại
- `500+`: lỗi server

## 10. DTO notes quan trọng cho mobile

## 10.1 Inconsistent level format
- `User.level`, `Vocabulary.level`: string (`N1..N6` hoặc có thể rỗng với data cũ)
- `Grammar.level`, `Kanji.level`: integer (`1..5`)

Khuyến nghị:
- Tạo mapper chuẩn hoá về enum nội bộ của app.

## 10.2 Field chính tả lịch sử
- API dùng `lession_id` (không phải `lesson_id`) ở nhiều endpoint learning/progress.
- Cần giữ đúng key để tương thích backend hiện tại.

## 10.3 Nullability
Nhiều field cũ có thể null/rỗng:
- `avatar`, `last_study_date`, `level` trong unit
- JSON fields có thể là `[]`, `{}` hoặc `null`

Khuyến nghị:
- `ignoreUnknownKeys = true`
- DTO dùng default value hợp lý.

## 11. Flow đề xuất cho app mobile

## 11.1 Onboarding
1. Register
2. Verify OTP
3. Login
4. Lưu token + profile vào secure storage

## 11.2 Home screen
1. `GET /api/users/stats/`
2. `GET /api/learning/lessons/?level=<target>`
3. `GET /api/learning/progress/?page=1&page_size=20`

## 11.3 Màn học unit
1. `GET /api/learning/units/{id}/detail/?page=1&page_size=20`
2. Render theo `unit_type`
3. Cập nhật tiến độ bằng `POST /api/learning/progress/`

## 11.4 Màn ôn Anki
1. `GET /api/learning/units/{id}/anki/next/`
2. Submit rating qua `POST /anki/review/`
3. Lặp tới khi user dừng

## 11.5 Màn luyện đề
1. Lấy exam từ `/api/n{level}/exams/`
2. Tạo/resume attempt
3. Lấy questions (`/exams/{id}/questions/`)
4. Lưu answer mỗi câu qua `/attempts/{id}/answers/`
5. Submit attempt
6. Load summary từ `/attempts/progress/`

## 12. Test checklist trước khi release mobile

## 12.1 Auth
- Login sai mật khẩu -> nhận message lỗi đúng
- Token hết hạn -> auto refresh thành công
- Refresh fail -> clear session + điều hướng login

## 12.2 Content
- List endpoint parse đúng envelope + pagination
- Unknown field không làm crash parser

## 12.3 Learning
- `progress` upsert hoạt động đúng (201 lần đầu, 200 lần sau)
- Anki review trả `next_card` đúng

## 12.4 Practice
- Lưu answer single + batch
- Submit chuyển trạng thái `IN_PROGRESS -> SUBMITTED`

## 12.5 Avatar
- Upload thành công theo flow presigned (khuyến nghị)
- Delete avatar clear đúng profile

## 13. Tham chiếu trong repo
- Tổng endpoint: `docs/api/endpoints.md`
- Avatar chi tiết: `docs/api/avatar-cloudflare.md`
- Practice chi tiết: `docs/api/practice.md`
- N-level dataset: `docs/api/n1.md`, `docs/api/n2.md`, `docs/api/n3.md`, `docs/api/n4.md`, `docs/api/n5.md`
- Anki theo unit: `docs/api/anki-unit-learning.md`
- Frontend integration (tổng quát): `docs/FRONTEND-INTEGRATION-GUIDE.md`
