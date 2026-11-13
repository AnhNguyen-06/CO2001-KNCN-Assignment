# Hợp đồng API và dữ liệu

Browser gọi /api/* cùng origin. Next.js chuyển tiếp sang PRESENCE_BACKEND_URL; nếu có PRESENCE_BACKEND_KEY, proxy tự thêm X-Presence-Key. Browser không nhận key.

## HTTP API

| Method và endpoint | Request | Response |
| --- | --- | --- |
| GET /api/health | — | status, storage, timezone, recognition |
| GET /api/workspace | — | members[], records[], exports[] từ SQLite |
| POST /api/registration/sample | JSON {image: dataURL} | accepted và quality; chưa ghi hồ sơ |
| POST /api/members | JSON {person_id, full_name, images:[3 dataURL]} | 201, outcome created hoặc already_registered |
| POST /api/recognition/sessions | — | token, generation |
| POST /api/recognition/sessions/{token}/frames?frame_id=N | binary JPEG | FrameResult + image_width, image_height, faces[].name |
| DELETE /api/recognition/sessions/{token} | — | stopped:true; gọi lặp an toàn |
| POST /api/exports/retry | — | scheduled:true |
| GET /api/exports/download | Query date? YYYY-MM-DD, member_id?, q? | .xlsx từ DB theo bộ lọc |

Registration chỉ thành công sau transaction và gallery reload. Retry cùng ID/tên/ba ảnh đã lưu không tạo thêm hồ sơ. ID trùng nội dung khác trả 409. Không có endpoint check-in tùy ý từ ID do client gửi; điểm danh đi qua xác nhận CV.

## Dữ liệu frontend

| Loại | Trường |
| --- | --- |
| Member | id, name, role, color, joinedAt, samples |
| AttendanceRecord | id, memberId, name, recordedAt, date, source:"camera" |
| Export state | attendance_date, data_revision, exported_revision, last_export_at, last_error, status |
| FrameResult | generation, frame_id, gallery_version, faces, events, processing_ms, stale, image_width, image_height |
| Face | bbox, landmarks, quality, match, track_id, state, name |
| Event | kind, message, data |

Role/color là metadata trình bày được suy ra; họ tên/ID và bản ghi lấy từ database. Không trả embedding hay ảnh trong workspace. Tọa độ bbox/landmark theo ảnh JPEG được gửi, chưa mirror; frontend chuyển tọa độ nếu preview mirror.

## Lỗi và giới hạn

Lỗi nghiệp vụ trả JSON {code,message}, 409 cho conflict/expired/busy, 422 cho ảnh và mẫu không hợp lệ. FastAPI validation có thể trả detail; helper frontend hỗ trợ cả hai. Request quá lớn trả 413, proxy mất backend trả 503 với mã BACKEND_UNAVAILABLE. Lỗi nội bộ trả thông báo chung.

| Code | Cách xử lý |
| --- | --- |
| INVALID_INPUT / INVALID_IMAGE | Kiểm tra trường nhập hoặc chụp lại |
| SAMPLE_NO_FACE / SAMPLE_MULTIPLE_FACES | Giữ đúng một mặt trong khung |
| SAMPLE_LOW_QUALITY | Điều chỉnh độ sáng, nét, khoảng cách hoặc tư thế |
| SAMPLE_IDENTITY_MISMATCH | Chụp lại ba mẫu cùng người |
| DUPLICATE_ID | Dùng ID đúng, kiểm tra hồ sơ hiện có |
| DUPLICATE_SAMPLE | Chụp lại các ảnh khác nhau |
| POSSIBLE_DUPLICATE_FACE | Kiểm tra danh tính đã đăng ký |
| SESSION_EXPIRED | Tắt/bật camera để tạo phiên mới |
| CAMERA_BUSY | Thử lại khi dịch vụ bớt tải |
| GALLERY_RELOAD_FAILED | Khôi phục gallery trước khi nhận diện |
| attendance_failed event | Chưa lưu; backend thử lại có giới hạn nhịp |
| export lỗi/pending | Điểm danh vẫn giữ; đóng Excel và retry |

Proxy/API giới hạn request 4 MiB, mỗi ảnh 1 MiB. Chỉ JPEG/PNG, tối đa 2400px một cạnh và 4 triệu pixel. Camera client mặc định JPEG 0.75, rộng tối đa 960px. Proxy timeout 25s. Request realtime chỉ có một frame đang chờ trên mỗi client.

## Python boundary

Kiểu thực tế nằm ở backend/presence_cv/types.py. BaselineSession.register nhận ID, tên, ba BGR images; process nhận FramePacket(generation, frame_id, captured_at, image_bgr) và optional is_current. Callback được kiểm tra trước/sau inference và trước khi ghi để loại phiên bị dừng.

Một inference executor sở hữu VisionEngine. Timestamp freshness dùng clock backend; không nhận clock browser. Mỗi phiên giữ tracking riêng. SQLite unique constraint là lớp cuối chống trùng giữa mọi phiên. close của child session không đóng exporter dùng chung; root session chịu trách nhiệm flush và đóng exporter khi server dừng.
