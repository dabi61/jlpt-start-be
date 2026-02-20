# Landing Page Style Guide (JLPT.codes)

## 1. Muc tieu
- Tai tao tinh than visual tu anh tham chieu: toi gian, sach, rong, de doc.
- Nhan dien ro tu khoa hoc ngon ngu: line-art den va accent cam.
- Chuyen doi thanh he thong style co the dung lai cho cac trang tiep theo.

## 2. DNA thi giac tu anh mau
- Khung tong: background sang, nhieu khoang trang, content can giua.
- Typography: heading dam, to, nhin ro hierarchy; body gon va de scan.
- Sac thai chinh:
  - Ink den dam cho text va line icon.
  - Cam am cho diem nhan (tu khoa, CTA).
  - Nen be/trang kem va xanh nhat cho lop phu tro.
- Minh hoa: ve net tay don gian, duong tron, icon chat bubble, laptop, nguoi hoc.

## 3. Design tokens da quy doi
- Mau:
  - `--bg: #fffdf7`
  - `--surface: #ffffff`
  - `--ink: #1c1d23`
  - `--muted: #5f6571`
  - `--line: #e8e0cf`
  - `--accent: #f59d1a`
  - `--accent-strong: #ee7f1a`
- Radius:
  - Card lon: `30px`
  - Card vua: `16px`
  - Pill/chip: `999px`
- Shadow:
  - `0 16px 40px rgba(17, 20, 28, 0.08)`
- Typography:
  - Heading: `Sora`
  - Body/UI: `Manrope`

## 4. Cau truc trang
- Header sticky:
  - Brand trai.
  - Menu giua (Courses/Mission/Approach/Research/Careers).
  - Nút API Docs ben phai.
- Hero 2 cot:
  - Cot trai: eyebrow + headline lon + CTA + benefit bullets.
  - Cot phai: line-art SVG minh hoa.
- Level strip:
  - Chip danh muc N5 -> N1 + module lien quan.
- Feature blocks:
  - 1 block lon mo ta gia tri cot loi.
  - 2 block nho cho approach.
- Research section:
  - 3 card thong ke gia tri ky thuat.
- Final CTA:
  - Mock mobile + call-to-action.

## 5. Motion & interaction
- Scroll reveal:
  - Khoi tao `opacity: 0`, `translateY(18px)`.
  - Khi vao viewport: fade + move len.
- Hero art:
  - Floating animation nhe (`6s`, ease-in-out, loop).
- Mobile nav:
  - Toggle menu giam complexity tren man hinh hep.

## 6. Quy tac mo rong
- Moi trang moi phai tai su dung token mau, radius, shadow.
- Heading quan trong chi dung accent cam cho 1-2 tu khoa.
- Uu tien line icon/SVG dong bo phong cach thay vi anh stock mau.
- CTA chinh luon dung gradient cam; CTA phu dung nut vien trang.
