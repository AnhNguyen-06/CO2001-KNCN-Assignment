# Deploy miễn phí với Vercel, Render và Neon

## Kiến trúc

```text
Browser webcam → Next.js trên Vercel → FastAPI + YuNet/SFace trên Render Free
                                              ↓
                                    PostgreSQL trên Neon Free
                                              ↓
                                    Excel tạo khi người dùng tải
```

Frontend cần PRESENCE_BACKEND_URL để tìm Python API. Backend cần DATABASE_URL để lưu hồ sơ/embedding/điểm danh trong Neon. Vercel triển khai thư mục frontend, Docker backend được build riêng trên Render.

Render Free có filesystem tạm và ngủ khi không hoạt động. Chế độ cloud dùng PostgreSQL và dựng workbook trong bộ nhớ lúc download. [Giới hạn Render Free](https://render.com/docs/free).

## 1. Tạo Neon

1. Đăng nhập Neon, chọn tạo project và gói Free. Đặt tên dễ nhận biết, ví dụ presence-attendance.
2. Chọn region gần backend Singapore nhất trong những region tài khoản cung cấp. Có thể chọn PostgreSQL 17, phiên bản đã dùng để kiểm thử local.
3. Dùng database/role mặc định của project hoặc tạo database riêng cho bài tập.
4. Bấm **Connect**, chọn đúng branch, database và role.
5. Bật **Connection pooling**, copy toàn bộ connection string dạng PostgreSQL URI. Giữ nguyên sslmode và channel_binding Neon cung cấp.
6. Lưu connection string ở biến môi trường DATABASE_URL của Render trong bước sau.

Backend tự tạo các bảng meta, persons, face_samples, attendance và export_state trong lần khởi động đầu tiên. Mỗi hồ sơ có ID duy nhất và ba embedding; UNIQUE(person_id, attendance_date) chống trùng điểm danh.

Connection string chứa mật khẩu database. Đặt nó trong environment của backend. Tham khảo [hướng dẫn lấy connection string của Neon](https://neon.com/docs/connect/connect-from-any-app).

Để xem dữ liệu sau khi đăng ký, mở SQL Editor của đúng database/branch:

```sql
SELECT person_id, full_name, created_at FROM persons;
SELECT person_id, count(*) AS sample_count FROM face_samples GROUP BY person_id;
SELECT person_id, full_name_snapshot, attendance_date, recorded_at FROM attendance;
```

Database Neon mới bắt đầu trống. Hồ sơ SQLite local có thể tiếp tục dùng local. Nhóm dự kiến tự đăng ký trên web sau deploy.

## 2. Tạo Render Web Service

Repo đã có backend/Dockerfile, backend/.dockerignore, runtime lockfile và render.yaml khai báo plan free.

Cách tạo qua dashboard:

1. Đăng nhập Render bằng GitHub, chọn **New → Web Service**, kết nối repo AnhNguyen-06/CO2001-KNCN-Assignment.
2. Chọn branch main.
3. Đặt **Root Directory** là backend.
4. Chọn **Language / Runtime** là Docker.
5. Đặt **Dockerfile Path** là ./Dockerfile và **Docker Build Context Directory** là ., tính tương đối với Root Directory.
6. Chọn **Region** Singapore và **Instance / Compute Plan** Free.
7. Dùng lệnh mặc định trong Dockerfile. Docker CMD tự đọc PORT của Render, bind 0.0.0.0 và chạy một Uvicorn worker.
8. Đặt **Health Check Path** là /api/health.
9. Thêm environment theo bảng dưới, rồi bấm Deploy Web Service.

| Biến trên Render | Giá trị |
| --- | --- |
| DATABASE_URL | Toàn bộ PostgreSQL URI copy từ Neon |
| PRESENCE_BACKEND_KEY | Một secret ngẫu nhiên do bạn giữ, dùng cùng giá trị trên Vercel |
| PRESENCE_EXPORT_MODE | download |
| PRESENCE_CV_THREADS | 1 |

Docker mặc định PRESENCE_DATA_DIR=/tmp/presence và dùng OpenCV headless. Hai model được tải và kiểm tra SHA-256 lúc build, có sẵn trong image lúc start. Ảnh camera xử lý trong bộ nhớ. PostgreSQL giữ dữ liệu qua restart/redeploy.

Tạo backend key trên máy local nếu cần:

```powershell
backend/.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

Chờ log báo Application startup complete và Uvicorn running. Mở URL Render cấp, ví dụ https://<service-name>.onrender.com/api/health.

Response cần có:

```json
{
  "status": "ready",
  "storage": "postgresql",
  "export_mode": "download",
  "timezone": "Asia/Ho_Chi_Minh",
  "recognition": "YuNet + SFace"
}
```

Nếu storage là sqlite, kiểm tra DATABASE_URL trên service và deploy lại trước khi thu dữ liệu nhóm. Khi đã có key, endpoint dữ liệu gọi trực tiếp thiếu X-Presence-Key trả 401; frontend proxy thêm key tại server.

Có thể dùng **New → Blueprint** và chọn repo để Render đọc render.yaml thay cho các bước cấu hình thủ công. Nhập DATABASE_URL và PRESENCE_BACKEND_KEY khi được yêu cầu. [Docker trên Render](https://render.com/docs/docker), [Blueprint specification](https://render.com/docs/blueprint-spec).

## 3. Kết nối Vercel

Bạn đã biết thao tác deploy frontend. Đặt Root Directory là frontend và thêm hai biến server-side:

| Biến trên Vercel | Giá trị |
| --- | --- |
| PRESENCE_BACKEND_URL | https://<service-name>.onrender.com |
| PRESENCE_BACKEND_KEY | Cùng secret đã đặt trên Render |

PRESENCE_BACKEND_URL là origin, bỏ phần /api và /api/health. Đặt biến cho Production và Preview nếu sử dụng cả hai, sau đó redeploy frontend. Browser gửi /api cùng origin, Next proxy gọi Python bằng secret. DATABASE_URL được dùng ở backend Render.

Mở https://<frontend-domain>/api/health để kiểm tra đường đi Vercel→Render. Kết quả phải giống health backend.

## 4. Chạy demo sau deploy

1. Mở website vài phút trước giờ trình bày để dịch vụ Free thức dậy.
2. Nếu thấy thông báo waking up, giữ trang mở. Frontend tự thử lại và có nút Retry connection.
3. Bạn đăng ký đầu tiên qua Members, nhập họ tên/MSSV, chụp ba góc nhẹ và Save profile.
4. Kiểm tra hồ sơ cùng ba mẫu trong Neon SQL Editor.
5. Mở Attendance, bật camera, giữ mặt ổn định đến khi báo thành công.
6. Kiểm tra Records và tải Excel.
7. Restart/redeploy backend, mở lại web. Hồ sơ và điểm danh phải còn trong Neon.
8. Đăng ký thêm 1–2 người trước buổi học, để 1–2 người đăng ký trực tiếp trong lúc trình bày.

Render Free ngủ sau 15 phút không có inbound traffic và có thể cần khoảng một phút để thức dậy. Proxy timeout 25 giây nên lần đầu có thể báo chờ, rồi frontend tự thử lại. Hạn mức Free của từng nền tảng cần theo dõi trong dashboard. [Render Free](https://render.com/docs/free).

Thời gian CV phụ thuộc CPU chia sẻ và mạng. Container local giới hạn 0.1 CPU/512 MB đã chạy model thật, nhưng thời gian trên Render/Neon cần đo sau deploy.

## 5. Xử lý lỗi

| Dấu hiệu | Kiểm tra |
| --- | --- |
| Build lỗi tải model | Xem log GitHub download/checksum, retry deploy |
| Module cv2 lỗi | Dùng Dockerfile và requirements-cloud.lock.txt của repo |
| Kết nối database thất bại | DATABASE_URL đúng branch/role/password, URI còn đủ SSL parameters |
| Health storage=sqlite | DATABASE_URL đang trống hoặc đặt sai service |
| Workspace báo401 | PRESENCE_BACKEND_KEY trên Render/Vercel phải trùng |
| Web chờ backend lâu | Mở health Render, xem log startup, đợi cold start rồi thử lại |
| Nhận diện chậm | Thử từng người, giữ mặt ổn định, ánh sáng tốt, kiểm tra mạng |
| Camera bị từ chối | Allow camera và dùng HTTPS |
| Excel ready to download | Dữ liệu đã lưu trong PostgreSQL, bấm Export Excel để tải workbook |

## 6. Chỉ deploy Vercel sẽ hoạt động đến đâu?

Landing và các trang Next.js có thể render, browser có thể xin quyền camera. Luồng đăng ký và điểm danh cần FastAPI để chạy YuNet/SFace và ghi database. Deploy frontend riêng hiện không khởi chạy Python service, nên các request /api sẽ thất bại nếu PRESENCE_BACKEND_URL chưa trỏ tới backend hoạt động.

127.0.0.1 trên Vercel là môi trường Vercel. Muốn frontend cloud gọi API trên laptop, laptop phải có endpoint HTTPS truy cập được từ cloud. Với cấu hình đã chọn, Render cung cấp endpoint này và Neon cung cấp database bền vững. SQLite đặt trên filesystem Vercel Functions không đáp ứng kiến trúc lưu trữ hiện tại. [Vercel về SQLite](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel).

## Phạm vi kiểm chứng

Mã nguồn hỗ trợ PostgreSQL/SQLite, cloud download, Docker Linux và retry cold start. Kiểm thử dùng PostgreSQL 17 trong Docker và backend Linux có giới hạn tài nguyên. Cần tài khoản/connection string của bạn để kiểm chứng trực tiếp Render/Neon sau deploy.

Luồng hiện tạo hồ sơ nhận diện bằng tên, ID và khuôn mặt. Email/password, phân quyền và liveness là các khả năng phát triển riêng. Nhóm dùng luồng đăng ký đã có cho bài tập.
