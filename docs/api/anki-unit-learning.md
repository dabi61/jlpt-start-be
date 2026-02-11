# Unit Anki Learning API

Tài liệu này mô tả bộ API học theo kiểu Anki cho từng `unit`.

## 1. Mục tiêu
- Mỗi user có lịch ôn riêng cho từng item trong unit.
- Dùng cơ chế giống Anki/SM-2: `again`, `hard`, `good`, `easy`.
- Trả response theo chuẩn envelope toàn hệ thống:
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

## 2. Endpoint

### 2.1 GET `/api/learning/units/{id}/anki/next/`
Lấy card tiếp theo cho user hiện tại trong unit.

Query params:
- `include_future` (optional, default=`true`): nếu chưa có card đến hạn thì lấy card gần nhất sắp đến hạn.

Response `data`:
- `unit`: thông tin unit.
- `sync`: kết quả đồng bộ card ban đầu.
  - `total_items`: tổng item lấy từ bảng detail của unit.
  - `created_cards`: số card mới tạo cho user hiện tại.
- `card`: card hiện tại (hoặc `null` nếu unit rỗng).
- `card_is_due`: `true` nếu card đang đến hạn.
- `stats`: thống kê queue.

### 2.2 POST `/api/learning/units/{id}/anki/review/`
Gửi kết quả trả lời cho card.

Request body:
```json
{
  "card_id": 1201,
  "rating": "good",
  "response_time_ms": 2400
}
```

Validation:
- `rating` bắt buộc, chỉ nhận: `again`, `hard`, `good`, `easy`.
- `card_id` phải thuộc đúng `user` và đúng `unit` đang học.

Response `data`:
- `unit`
- `reviewed_card`: card sau khi cập nhật scheduler.
- `next_card`: card tiếp theo trong hàng đợi.
- `next_card_is_due`
- `stats`

### 2.3 GET `/api/learning/units/{id}/anki/stats/`
Lấy thống kê queue học của user trong unit.

Response `data.stats`:
- `total_cards`
- `due_now`
- `new_cards`
- `learning_cards`
- `relearning_cards`
- `review_cards`
- `next_due_at`

## 3. Nguồn dữ liệu card
- `unit_type=vocabulary`: lấy item từ `UnitWordDetail`.
- `unit_type=grammar`: lấy item từ `UnitGrammarDetail`.
- `unit_type=kanji`: lấy item từ `UnitKanjiDetail`.
- Nếu unit_type bất thường hoặc rỗng: fallback lấy cả 3 bảng.

Mỗi item tạo 1 card duy nhất theo key:
- `(unit_id, user_id, item_type, item_id)`

## 4. Trạng thái card
- `new`: card chưa học.
- `learning`: đang đi qua các bước học phút.
- `relearning`: card review bị quên, quay về học lại.
- `review`: card đã tốt nghiệp, ôn theo số ngày.

## 5. Scheduler (Anki style)

Tham số hiện tại:
- Learning steps: `1m`, `10m`
- Relearning steps: `10m`
- Graduating interval: `1d`
- Easy interval: `4d`
- Hard factor: `1.2`
- Easy bonus: `1.3`
- Review fail factor (`again`): `0.5`
- Min ease factor: `1.3`

### 5.1 Rating `again`
- Nếu đang `review`: tăng `lapses`, giảm ease, chuyển `relearning`, due theo bước relearning.
- Nếu đang `learning/relearning`: quay lại bước đầu của learning/relearning.
- Nếu đang `new`: vào `learning` bước đầu.

### 5.2 Rating `hard`
- `new/learning`: tiến chậm trong learning steps.
- `relearning`: tiến chậm trong relearning steps.
- `review`: tăng interval nhẹ (`*1.2`) và giảm ease nhẹ.

### 5.3 Rating `good`
- `new/learning`: đi tiếp step; hết step thì graduate sang `review`.
- `relearning`: đi tiếp step; hết step thì quay lại `review`.
- `review`: tăng interval theo ease factor.

### 5.4 Rating `easy`
- Tăng ease factor.
- `new/learning`: graduate thẳng sang `review` với easy interval.
- `relearning`: quay lại `review` với interval tốt hơn.
- `review`: tăng interval mạnh hơn (kèm easy bonus).

## 6. Thứ tự ưu tiên lấy card
Khi có nhiều card đến hạn:
1. `learning`
2. `relearning`
3. `review`
4. `new`

Sau đó sort theo `due_at`, rồi `id`.

## 7. Logging
Mỗi lần review lưu log vào `UnitAnkiReviewLog`:
- rating
- previous/next state
- previous/next interval
- previous/next ease
- response_time_ms
- reviewed_at

## 8. Lỗi thường gặp
- `400` + message `"Card does not belong to this user or unit."` khi gửi `card_id` sai phạm vi.
- `400` validation message nếu `rating` không hợp lệ.

## 9. Flow tích hợp frontend
1. Vào màn học unit -> gọi `GET /anki/next/`.
2. Render `data.card.content`.
3. User chọn nút `again/hard/good/easy`.
4. Gọi `POST /anki/review/`.
5. Dùng `data.next_card` để render ngay card kế tiếp.
6. Cập nhật counter bằng `data.stats`.
