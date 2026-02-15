# Avatar Upload Với Cloudflare R2 (Presigned URL)

Tài liệu này mô tả cách upload avatar user bằng Cloudflare R2 (S3-compatible) với presigned URL.

## 1. Mục tiêu
- Frontend upload file trực tiếp lên R2 (không stream file qua backend).
- Backend chỉ cấp presigned URL, xác nhận object tồn tại, và lưu URL public vào `users.User.avatar`.
- Backend lưu thêm `avatar_image_id` (thực chất là **object key**) để quản lý vòng đời ảnh.

## 2. Biến môi trường

Thêm vào `.env`:

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

Ghi chú:
- `R2_PUBLIC_BASE_URL` nên là custom domain đã bind vào bucket (ví dụ `https://storage.jlpt.codes`).
- Direct upload từ browser cần cấu hình **CORS** cho bucket để cho phép `PUT` từ domain frontend.

## 3. API Flow

### Option A (khuyến nghị): Upload trực tiếp lên R2 (presigned URL)

### Bước 1: Lấy upload URL
- `POST /api/users/avatar/upload-url/`
- Request body (optional):
```json
{
  "content_type": "image/png",
  "filename": "avatar.png"
}
```
- Trả về:
```json
{
  "image_id": "avatar/<user_id>/<uuid>.png",
  "upload_url": "https://<account_id>.r2.cloudflarestorage.com/<bucket>/avatar/<user_id>/<uuid>.png?...",
  "method": "PUT",
  "headers": { "Content-Type": "image/png" },
  "public_url": "https://storage.jlpt.codes/avatar/<user_id>/<uuid>.png",
  "expires_in": 600,
  "max_bytes": 5242880
}
```

### Bước 2: Frontend upload trực tiếp
- `PUT` tới `upload_url`
- Body: bytes của file (không phải multipart)
- Header: `Content-Type` (nếu backend trả về `headers`)

### Bước 3: Confirm và lưu avatar
- `POST /api/users/avatar/confirm/`
```json
{
  "image_id": "avatar/<user_id>/<uuid>.png"
}
```

Backend sẽ:
- `HEAD` object để đảm bảo object đã tồn tại.
- Lưu `public_url` vào `user.avatar`.
- Lưu `image_id` vào `user.avatar_image_id`.
- Xóa avatar cũ (best-effort) nếu thuộc prefix `avatar/`.

### Option B: Upload qua backend (1 API call)
Nếu bạn không muốn dùng presigned URL, backend hỗ trợ upload ảnh qua `multipart/form-data` và backend sẽ upload lên R2 thay bạn.

- `PUT /api/users/avatar/` (hoặc `POST /api/users/avatar/`)
- Content-Type: `multipart/form-data`
- Field:
  - `file`: file ảnh (hoặc `avatar`)

Response:
```json
{
  "avatar": "https://storage.jlpt.codes/avatar/<user_id>/<uuid>.png",
  "avatar_image_id": "avatar/<user_id>/<uuid>.png"
}
```

### Bước 4: Xóa avatar
- `DELETE /api/users/avatar/`
- Xóa object trên R2 theo key rồi clear `avatar` và `avatar_image_id`.

## 4. Lỗi thường gặp
- `503`: thiếu config R2 (`R2_*`).
- `400`: confirm quá sớm (object chưa upload xong) hoặc file vượt quá `R2_MAX_UPLOAD_BYTES`.
- `502`: lỗi gọi S3 API (credential sai, bucket không tồn tại, quyền không đủ).

## 5. Security
- Không hardcode key vào source code.
- Key dùng upload nên giới hạn quyền (chỉ bucket cần thiết).
- Nếu key bị lộ, rotate credential ngay trên Cloudflare Dashboard.
