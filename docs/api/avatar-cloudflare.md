# Avatar Upload Với Cloudflare Images

Tài liệu này mô tả cách tích hợp upload avatar user bằng Cloudflare Images.

## 1. Mục tiêu
- Frontend upload file trực tiếp lên Cloudflare (không đi qua backend file stream).
- Backend chỉ cấp upload URL, xác nhận ảnh, và lưu URL vào `users.User.avatar`.
- Mỗi user lưu thêm `avatar_image_id` để quản lý vòng đời ảnh.

## 2. Biến môi trường

Thêm vào `.env`:

```env
CF_ACCOUNT_ID=your_account_id
CF_IMAGES_API_TOKEN=your_cloudflare_images_api_token
CF_IMAGES_AVATAR_VARIANT=avatar
CF_IMAGES_ACCOUNT_HASH=
CF_IMAGES_TIMEOUT=15
```

Ghi chú:
- `CF_IMAGES_ACCOUNT_HASH` là optional. Nếu không có, backend sẽ lấy URL từ `result.variants` do Cloudflare trả về.
- Cần tạo sẵn variant `avatar` trên Cloudflare Images Dashboard.

## 3. API Flow

### Bước 1: Lấy upload URL
- `POST /api/users/avatar/upload-url/`
- Trả về:
```json
{
  "image_id": "uuid-or-id",
  "upload_url": "https://upload.imagedelivery.net/..."
}
```

### Bước 2: Frontend upload file trực tiếp
- `POST` tới `upload_url`
- `multipart/form-data` với field `file`

### Bước 3: Confirm và lưu avatar
- `POST /api/users/avatar/confirm/`
```json
{
  "image_id": "uuid-or-id"
}
```

Backend sẽ:
- Check ảnh có tồn tại và không còn `draft`.
- Lấy URL variant `avatar` và lưu vào `user.avatar`.
- Lưu `user.avatar_image_id`.
- Nếu user đã có avatar cũ thì xóa ảnh cũ (best-effort).

### Bước 4: Xóa avatar
- `DELETE /api/users/avatar/`
- Xóa ảnh trên Cloudflare theo `avatar_image_id` rồi clear `avatar` và `avatar_image_id`.

## 4. Lỗi thường gặp
- `503`: chưa cấu hình Cloudflare (`CF_ACCOUNT_ID` / `CF_IMAGES_API_TOKEN`).
- `400`: ảnh chưa upload xong (`draft=true`) khi gọi confirm.
- `502`: Cloudflare API trả lỗi upstream.

## 5. Security
- Không hardcode token vào source code.
- API token chỉ cấp quyền Images tối thiểu.
- Nếu token bị lộ, rotate token ngay trên Cloudflare Dashboard.
