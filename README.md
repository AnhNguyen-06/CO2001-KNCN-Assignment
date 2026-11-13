# Presence — Webcam Facial Recognition Attendance

Ứng dụng điểm danh cho môn Kỹ năng chuyên nghiệp cho Kỹ sư, HCMUT. Frontend Next.js đã tích hợp FastAPI, YuNet + SFace, SQLite/PostgreSQL và Excel. Giao diện tiếng Anh theo [mẫu thiết kế](docs/authkit.com-DESIGN.md), dùng Inter/Manrope self-hosted.

## Chạy ứng dụng web

Mở hai terminal từ thư mục gốc. Môi trường hiện tại đã cài sẵn dependencies và model.

Terminal 1:

```powershell
cd backend
.venv/Scripts/python.exe -m uvicorn presence_cv.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Mở http://127.0.0.1:3000. Nếu các server này đã chạy, dùng ngay đường dẫn đó. Đóng cửa sổ CV standalone trước khi dùng webcam trên web.

**Luồng sử dụng:** Register member → họ tên + ID/MSSV → bật camera → chụp chính diện, hơi trái, hơi phải → Review profile → Save profile → Attendance → Turn on camera → giữ mặt ổn định → Attendance successful → Records / Export Excel.

[Hướng dẫn demo chi tiết và xử lý lỗi](docs/WEB_DEMO.md) · [Cài backend từ đầu](backend/README.md) · [Frontend](frontend/README.md) · [Deploy Vercel + backend](docs/DEPLOYMENT.md).

## Dữ liệu và hành vi

- Website bắt đầu trống, không seed thành viên, ảnh hay lượt điểm danh. Hồ sơ tự chụp thử đã được xóa.
- Họ tên, ID dạng chuỗi, ba embedding/người và điểm danh lưu trong database thật. Local dùng SQLite tại `backend/var/attendance.sqlite3`; khi có `DATABASE_URL`, backend dùng PostgreSQL của Neon.
- Ảnh webcam chỉ dùng trong bộ nhớ để kiểm tra và trích xuất embedding. Không ghi ảnh gốc vào database hoặc localStorage.
- Mỗi ID chỉ có một bản ghi/ngày theo Asia/Ho_Chi_Minh, kể cả sau restart hoặc khi nhiều trình duyệt gửi đồng thời.
- Thông báo thành công chỉ xuất hiện sau commit. Local tự cập nhật Excel tại `backend/var/exports/`. Cloud dùng `PRESENCE_EXPORT_MODE=download`, dựng workbook từ DB khi tải.
- Trình duyệt chỉ lưu tùy chọn giao diện. Xóa localStorage không xóa hồ sơ/điểm danh.
- Đăng ký hiện tạo hồ sơ nhận diện bằng họ tên, ID và khuôn mặt. Bản này chưa có đăng nhập email/mật khẩu hay phân quyền quản trị.

## Kiến trúc

```text
Browser webcam → Next.js /api/* → FastAPI → YuNet / SFace → SQLite hoặc PostgreSQL
                                                         └→ Excel từ database
```

Browser sở hữu camera; backend không mở webcam của server. Next.js proxy cùng origin giúp dùng cùng luồng ở localhost và khi deploy. Cấu hình miễn phí được chọn là Vercel frontend, Render Free chạy Docker API và Neon Free giữ PostgreSQL. Backend Linux dùng OpenCV headless, một inference thread. Frontend tự thử lại khi Render đang thức dậy.

## Deploy miễn phí

Repo có `backend/Dockerfile` và `render.yaml` cho Render Free. Tạo Neon, đặt `DATABASE_URL`/`PRESENCE_BACKEND_KEY` trên Render, rồi nối Vercel bằng `PRESENCE_BACKEND_URL`/cùng key. Hướng dẫn từng bước và câu trả lời về chỉ deploy Vercel ở [DEPLOYMENT](docs/DEPLOYMENT.md).

## Kiểm tra

Từ `backend/`:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check presence_cv tools tests
.venv/Scripts/python.exe -m pip check
```

Từ `frontend/`:

```powershell
npm run typecheck
npm run build
npm run test:e2e
```

Chuẩn bị dữ liệu công khai cho model/browser test theo [frontend README](frontend/README.md). Test dùng database riêng, không thêm tài khoản vào database ứng dụng. Phạm vi và kết quả xem [TEST_PLAN](docs/TEST_PLAN.md). Nhóm sẽ đăng ký trên web sau; độ chính xác của bốn thành viên và điều kiện lớp học cần đo bằng lượt thử thật.

## Nhóm và trách nhiệm

| Thành viên | Phụ trách |
| --- | --- |
| Quang Anh | Computer Vision, UI, tích hợp |
| Lâm | SQLite, chống trùng, Excel |
| Ân | Đăng ký, dữ liệu và kiểm thử hiện trường |
| Hoàng | Môi trường, hướng dẫn, báo cáo, slide, video |

Không hardcode danh tính nhóm vào mã nguồn. Họ tên/MSSV chính xác được nhập khi đăng ký và bổ sung riêng vào báo cáo.

## Tài liệu

| Tài liệu | Nội dung |
| --- | --- |
| [WEB_DEMO](docs/WEB_DEMO.md) | Bắt đầu từ website sạch, đăng ký và demo thật |
| [DEPLOYMENT](docs/DEPLOYMENT.md) | Frontend Vercel, Python backend, lưu trữ và cấu hình |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Camera, HTTP, worker, database |
| [INTERFACES](docs/INTERFACES.md) | API và quy ước dữ liệu |
| [STATES](docs/STATES.md) · [RULES](docs/RULES.md) | Trạng thái và quy tắc nghiệp vụ |
| [CV_BASELINE](docs/CV_BASELINE.md) | Model, ngưỡng khởi đầu, bằng chứng baseline |
| [TEST_PLAN](docs/TEST_PLAN.md) | Kiểm thử tự động và đo hiện trường |
| [PROJECT_SCOPE](docs/PROJECT_SCOPE.md) · [TASKS](docs/TASKS.md) | Phạm vi và phân công bốn ngày |
| [UI_SPEC](docs/UI_SPEC.md) · [DECISIONS](docs/DECISIONS.md) | Thiết kế và quyết định kỹ thuật |
| [DEMO_SCRIPT](docs/DEMO_SCRIPT.md) | Kịch bản trình bày |

Dữ liệu cá nhân, embeddings, SQLite, exports, model weights và test artifacts được loại khỏi Git. RGB face recognition hiện chưa có liveness; cần công bố kết quả thử ảnh điện thoại trong báo cáo.
