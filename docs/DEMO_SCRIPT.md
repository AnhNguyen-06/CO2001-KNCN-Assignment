# Kịch bản demo và bộ nộp

Hướng dẫn thao tác đầy đủ ở [WEB_DEMO](WEB_DEMO.md). Hướng dẫn cloud ở [DEPLOYMENT](DEPLOYMENT.md).

## Demo 1–2 phút

| Thời lượng | Nội dung |
| --- | --- |
| 0–15s | Mở web, giới thiệu đăng ký trước rồi tự động điểm danh |
| 15–55s | Một thành viên chưa đăng ký nhập tên/MSSV, chụp3 góc nhẹ, review và save |
| 55–80s | Bật Attendance, cùng người vào khung, hiện tên và attendance successful |
| 80–100s | Tắt/bật lại, already checked in; reload vẫn còn dữ liệu |
| 100–120s | Tải Excel, đối chiếu tên/ID/giờ; nói rõ giới hạn liveness |

Trước buổi học bạn và 1–2 người có thể đăng ký trước, để1–2 người đăng ký trực tiếp trên lớp. Dành một người chưa điểm danh trong ngày để có bản ghi mới khi demo.

## Câu hỏi cần chuẩn bị

- Vì sao dùng YuNet/SFace pretrained thay vì train model hoặc gọi API?
- Ba ảnh được biến thành embedding thế nào? Thêm thành viên có đổi weights không?
- Threshold, margin và temporal confirmation khác nhau ở đâu?
- Vì sao SQLite là nguồn dữ liệu chính và Excel là đầu ra?
- Vì sao reload/restart không tạo trùng? UNIQUE ID/ngày bảo vệ thế nào?
- Người lạ, nhiều mặt, thiếu sáng hoặc ảnh điện thoại được xử lý ra sao?
- Vercel chạy phần nào, Python/DB chạy ở đâu?
- Hồ sơ nhận diện hiện khác tài khoản có đăng nhập/phân quyền thế nào?

## Bộ nộp

Mã nguồn và lockfiles, manifest/license model, README cài đặt, mô tả kiến trúc, kết quả kiểm thử, báo cáo, slide và video. Không nộp DB/embedding/ảnh cá nhân lên repo public. Phân biệt kết quả test công khai tự động với số liệu hiện trường của nhóm; không điền số đo chưa thực hiện.
