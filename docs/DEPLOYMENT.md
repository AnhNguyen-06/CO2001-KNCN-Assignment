# Triển khai frontend Vercel và Python backend

## Mô hình triển khai

```text
Browser HTTPS → Next.js trên Vercel → Python FastAPI HTTPS
                                      ├─ YuNet + SFace trên CPU
                                      └─ persistent volume: SQLite + Excel
```

Code đã có proxy và biến môi trường cho mô hình này. Chưa deploy hoặc push remote trong lần tích hợp này; chủ dự án sẽ cung cấp repo sau khi kiểm tra.

SQLite là database thật dạng file. File cần nằm trên ổ đĩa bền vững của backend. Vercel Functions không cung cấp ổ đĩa chia sẻ bền vững cho SQLite trong kiến trúc này; vì vậy deploy riêng frontend lên Vercel không đủ để chạy toàn bộ hệ thống. Xem [giải thích chính thức của Vercel](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel).

## Backend

Chuẩn bị một host Python luôn chạy, HTTPS và persistent volume. Với quy mô nhóm nhỏ, chạy một process/worker để mọi lease, gallery và model cùng runtime. Chưa hỗ trợ chia tải nhiều instance.

1. Đưa mã backend và manifest/license lên host; cài Python 3.13 và dependencies theo backend/README.md.
2. Chạy python main.py setup-models ở thư mục backend để tải hai model đúng checksum. Dùng Linux cần cung cấp thư viện hệ thống mà opencv-python yêu cầu; xác minh import cv2 và lệnh doctor trên image/host thực tế.
3. Mount một volume bền vững, ví dụ /data/presence. Cấp quyền ghi cho process Python.
4. Đặt biến môi trường của dịch vụ:

```text
PRESENCE_DATA_DIR=/data/presence
PRESENCE_BACKEND_KEY=<random-secret-shared-only-with-Next>
```

5. Chạy từ backend, thay PORT bằng cổng host cấp:

```sh
python -m uvicorn presence_cv.api:app --host 0.0.0.0 --port 8000 --workers 1
```

6. Gắn HTTPS/domain qua host hoặc reverse proxy. Kiểm tra /api/health trả ready. Các endpoint dữ liệu gọi trực tiếp thiếu X-Presence-Key phải trả 401 khi đã cấu hình key.
7. Thử restart/redeploy backend và xác minh hồ sơ/bản ghi vẫn còn. Chụp backup bằng SQLite backup API hoặc dừng service trước khi copy DB; không chỉ copy file SQLite chính trong lúc WAL đang ghi.

Các biến backend lấy từ environment thực tế của process. File .env.example là mẫu tham khảo; Uvicorn command trên không tự đọc .env. Không bật --reload trong production.

Host cần truy cập được từ Vercel. Địa chỉ127.0.0.1:8000 trên Vercel trỏ vào môi trường Vercel, không trỏ về laptop của bạn. Nếu dùng backend laptop cho demo từ web public cần endpoint HTTPS có thể truy cập từ cloud và giữ laptop/server đang chạy; độ ổn định phụ thuộc mạng.

## Frontend Vercel

Sau khi GitHub repo được tạo và source đã push:

| Thiết lập | Giá trị |
| --- | --- |
| Root Directory | frontend |
| Framework | Next.js |
| Install command | npm ci |
| Build command | npm run build |
| Output | Mặc định Next.js |
| PRESENCE_BACKEND_URL | https://<backend-domain>, không thêm /api |
| PRESENCE_BACKEND_KEY | Cùng secret của backend |

Đặt hai biến ở môi trường Production, và Preview nếu cần test preview. Redeploy sau khi đổi env. Không thêm tiền tố NEXT_PUBLIC; key chỉ được Next route handler sử dụng ở server. Tham khảo [Next.js trên Vercel](https://vercel.com/docs/frameworks/full-stack/nextjs) và [environment variables](https://vercel.com/docs/environment-variables).

Browser gọi /api cùng origin; chỉ Next server gọi backend, không cần mở CORS cho camera client. Mỗi frame chỉ một request đang chờ, mỗi ảnh nhỏ hơn 1 MiB, request tổng tối đa 4 MiB. Proxy timeout 25s; xử lý realtime cần nhanh hơn nhiều để đủ bằng chứng xác nhận. Không cam kết nhận diện dưới 1 giây qua Internet trước khi đo host/mạng thực.

## Kiểm tra sau deploy

1. /api/health của frontend trả ready.
2. Website mới không có tài khoản seed.
3. Đăng ký hồ sơ bằng 3 ảnh thật; Members hiển thị đúng tên/ID.
4. Nhận diện tạo 1 bản ghi; bật/tắt lại không tạo trùng.
5. Refresh/trình duyệt khác đọc cùng hồ sơ và bản ghi.
6. Restart backend vẫn còn dữ liệu; Excel tải đúng từ DB.
7. Thử người chưa đăng ký, camera denied và backend unavailable.
8. Thử đăng ký live qua mạng lớp trước giờ trình bày.

Dùng cùng backend và cùng PRESENCE_DATA_DIR để giữ hồ sơ đã đăng ký. Nếu chọn backend/database mới thì dữ liệu không tự chuyển theo mã nguồn frontend.

## Phạm vi bản hiện tại

Đăng ký và điểm danh dùng dữ liệu thật, nhưng workspace hiện chưa có xác thực đăng nhập hay quyền đọc/xuất riêng. Người truy cập link có thể đăng ký và xem danh sách/lịch sử. Shared backend key chỉ bảo vệ tuyến server-to-server, không thay thế quyền người dùng.

Đây là bản tích hợp cho demo nhóm nhỏ, chưa phải hệ thống quản lý danh tính công khai hoàn chỉnh. Để mở rộng vận hành cần xác thực/phân quyền, chống lạm dụng, chính sách dữ liệu và đánh giá liveness riêng. Các yêu cầu đó không được giả lập trong giao diện hiện tại.
