# Avatar Upload Với Cloudflare R2 (Cho Người Mới)

Tài liệu này mô tả cách upload avatar user lên Cloudflare R2 trong dự án.

Bạn có 2 cách upload:
1) Upload trực tiếp lên R2 bằng **presigned URL** (thường dùng cho web frontend).
2) Upload qua **backend API** (dễ dùng nhất, 1 API call, phù hợp mobile/server).

## 1. Avatar Được Lưu Ở Đâu?

Khi upload xong, backend sẽ lưu:
- `users.User.avatar`: public URL (để app hiển thị ảnh).
- `users.User.avatar_image_id`: object key trong R2 (để xoá/thay thế ảnh).

Ví dụ key: `avatar/<user_id>/<uuid>.png`

## 2. Chuẩn Bị: Lấy Access Token Để Gọi API

Các endpoint avatar đều yêu cầu đăng nhập.

1) Gọi login:
```bash
curl -X POST "https://jlpt.codes/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YOUR_PASSWORD"}'
```

2) Lấy token ở:
- `data.access.token`

3) Khi gọi các API bên dưới, gửi header:
- `Authorization: Bearer <ACCESS_TOKEN>`

## 3. Cách Dễ Nhất: Upload Qua Backend API (1 API Call)

Endpoint:
- `PUT /api/users/avatar/`
- (tuỳ chọn) `POST /api/users/avatar/` (alias, nếu client không tiện gửi multipart PUT)

### 3.1 Upload Bằng Raw Bytes (Không Multipart)

Đây là cách đúng nếu client của bạn “không phải multipart form-data”.

Yêu cầu:
- Header `Content-Type` nên là `image/png` hoặc `image/jpeg` hoặc `image/webp` hoặc `image/gif`.
- Nếu bạn chỉ gửi `Content-Type: application/octet-stream` thì bắt buộc cung cấp tên file có đuôi qua `X-Filename` hoặc `?filename=...`.

Ví dụ `curl` (khuyến nghị):
```bash
curl -X PUT "https://jlpt.codes/api/users/avatar/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: image/png" \
  --data-binary "@/path/to/avatar.png"
```

Ví dụ `curl` với `application/octet-stream`:
```bash
curl -X PUT "https://jlpt.codes/api/users/avatar/?filename=avatar.png" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@/path/to/avatar.png"
```

Ví dụ Postman:
1) Method: `PUT`
2) URL: `https://jlpt.codes/api/users/avatar/`
3) Headers:
`Authorization: Bearer <ACCESS_TOKEN>`
`Content-Type: image/png`
4) Body:
Chọn `binary` rồi chọn file ảnh.

Test nhanh trên Swagger UI:
1) Mở `PUT /api/users/avatar/` rồi bấm `Try it out`.
2) Ở dropdown `Request body content type`, chọn `multipart/form-data`.
3) Field `file` sẽ xuất hiện để chọn ảnh từ máy.
4) Nếu không thấy field, hard refresh trình duyệt (`Cmd+Shift+R`) hoặc restart server.

Ví dụ Node.js (fetch):
```js
import fs from "node:fs";

const token = process.env.ACCESS_TOKEN;
const bytes = fs.readFileSync("./avatar.png");

const res = await fetch("https://jlpt.codes/api/users/avatar/", {
  method: "PUT",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "image/png",
  },
  body: bytes,
});

console.log(await res.json());
```

Ví dụ Python (`requests`):
```py
import requests

token = "ACCESS_TOKEN"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "image/png"}

with open("avatar.png", "rb") as f:
    r = requests.put("https://jlpt.codes/api/users/avatar/", headers=headers, data=f)

print(r.status_code)
print(r.json())
```

Response (đã bọc envelope):
```json
{
  "meta": { "code": 200, "type": "SUCCESS", "message": "Request successful." },
  "data": {
    "avatar": "https://storage.jlpt.codes/avatar/<user_id>/<uuid>.png",
    "avatar_image_id": "avatar/<user_id>/<uuid>.png"
  }
}
```

Kiểm tra nhanh:
- Gọi `GET /api/users/profile/` để xem field `avatar` đã đổi chưa.
- Hoặc mở URL trong `data.avatar` để xem ảnh.

### 3.2 Upload Bằng Multipart/Form-Data (Tuỳ Chọn)

Nếu bạn dùng form-data (vd HTML form), gửi field `file`:
```bash
curl -X PUT "https://jlpt.codes/api/users/avatar/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@/path/to/avatar.png"
```

## 4. Upload Trực Tiếp Lên R2 (Presigned URL)

Cách này có 3 bước. File sẽ upload **thẳng lên R2**, backend chỉ cấp link upload và “confirm”.

### 4.1 Bước 1: Xin Upload URL

Endpoint:
- `POST /api/users/avatar/upload-url/`

Body có thể rỗng, hoặc gửi để backend gợi ý đuôi file và Content-Type:
```json
{
  "content_type": "image/png",
  "filename": "avatar.png"
}
```

Ví dụ `curl`:
```bash
curl -X POST "https://jlpt.codes/api/users/avatar/upload-url/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"content_type":"image/png","filename":"avatar.png"}'
```

Response (envelope):
```json
{
  "meta": { "code": 200, "type": "SUCCESS", "message": "Request successful." },
  "data": {
    "image_id": "avatar/<user_id>/<uuid>.png",
    "upload_url": "https://<account_id>.r2.cloudflarestorage.com/<bucket>/avatar/<user_id>/<uuid>.png?...",
    "method": "PUT",
    "headers": { "Content-Type": "image/png" },
    "public_url": "https://storage.jlpt.codes/avatar/<user_id>/<uuid>.png",
    "expires_in": 600,
    "max_bytes": 5242880
  }
}
```

Giải thích nhanh:
- `upload_url`: link tạm thời để **upload bytes** (hết hạn sau `expires_in` giây).
- `image_id`: key để dùng ở bước confirm.
- `public_url`: link public sau khi confirm.

### 4.2 Bước 2: PUT Bytes Lên `upload_url`

Bạn upload file tới `upload_url` (không phải tới domain backend).

Ví dụ `curl`:
```bash
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/png" \
  --data-binary "@/path/to/avatar.png"
```

Kỳ vọng:
- HTTP 200/204 từ R2 (tuỳ cấu hình)

### 4.3 Bước 3: Confirm Để Backend Set Avatar

Endpoint:
- `POST /api/users/avatar/confirm/`

Body:
```json
{ "image_id": "avatar/<user_id>/<uuid>.png" }
```

Ví dụ `curl`:
```bash
curl -X POST "https://jlpt.codes/api/users/avatar/confirm/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"image_id\":\"$IMAGE_ID\"}"
```

Response sẽ trả về `avatar` và `avatar_image_id` (envelope), giống cách upload qua backend.

## 5. Xoá Avatar

Endpoint:
- `DELETE /api/users/avatar/`

Ví dụ `curl`:
```bash
curl -X DELETE "https://jlpt.codes/api/users/avatar/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 6. Giới Hạn, Lỗi Thường Gặp, Và Cách Fix

Giới hạn:
- Dung lượng tối đa: `R2_MAX_UPLOAD_BYTES` (mặc định 5 MiB).
- Định dạng khuyến nghị: PNG/JPEG/WEBP/GIF.

Lỗi thường gặp:
- `401`: thiếu/ sai token. Hãy kiểm tra header `Authorization: Bearer ...`.
- `503`: backend chưa cấu hình R2 (`R2_*`).
- `400` khi confirm: confirm quá sớm hoặc object chưa upload xong.
- `415`: raw-bytes upload nhưng `Content-Type` không phải `image/*` (hoặc `application/octet-stream`).
- `502`: lỗi gọi S3 API (key sai, bucket sai, thiếu quyền).

## 7. CORS (Chỉ Cần Khi Upload Từ Browser)

Nếu upload trực tiếp từ browser bằng presigned URL, bucket R2 cần CORS cho phép `PUT` từ domain frontend.
Nếu upload từ backend/mobile/server, thường không cần CORS.

## 8. Biến Môi Trường (Backend)

Thêm vào `.env` của backend:
```env
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_REGION=auto
R2_BUCKET_NAME=your_bucket_name
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_PUBLIC_BASE_URL=https://storage.jlpt.codes
R2_AVATAR_PREFIX=avatar/
R2_PRESIGNED_EXPIRES=600
R2_MAX_UPLOAD_BYTES=5242880
```

Lưu ý bảo mật:
- Không nhúng `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` vào client (frontend/mobile).
- Nếu lỡ lộ key, rotate credential trong Cloudflare Dashboard.
