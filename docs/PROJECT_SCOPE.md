# Phạm vi và điều kiện thực hiện

## Hiện trạng tích hợp

FE Next.js đã nối Python FastAPI, YuNet/SFace, SQLite và Excel. Luồng web không còn mock profiles/check-ins. Chủ dự án yêu cầu website sạch để đăng ký đầu tiên, rồi1–2 thành viên đăng ký trước và 1–2 người đăng ký trực tiếp trên lớp. Họ tên, ID và face embeddings lưu ở backend. Kiểm thử tự động dùng dữ liệu công khai ở DB riêng; nhóm sẽ đăng ký trực tiếp sau.

Bản hiện tại tạo hồ sơ nhận diện thực; email/password, phân quyền và liveness chưa thuộc chức năng đã hoàn thành. Deploy Vercel cần Python backend có HTTPS và storage bền vững riêng. Xem WEB_DEMO và DEPLOYMENT.

## Mục tiêu

Hoàn thành ứng dụng có thể demo bằng webcam trên laptop trong bốn ngày, kèm kết quả kiểm thử thật, hướng dẫn, báo cáo, slide và video 1–2 phút. Theo yêu cầu mới, frontend là web tiếng Anh bằng Next.js App Router, thực hiện theo trình tự frontend → CV → tích hợp. Ngày 1–4 được tính từ thời điểm bắt đầu triển khai đã thống nhất.

## Luồng sử dụng

1. Mở ứng dụng và kiểm tra trạng thái model, database.
2. Đăng ký thành viên nếu danh sách còn trống.
3. Bấm bật camera.
4. Thành viên bước vào khung hình.
5. Ứng dụng phát hiện mặt, nhận diện và xác nhận kết quả ổn định.
6. Nếu ID chưa điểm danh hôm nay, lưu bản ghi vào SQLite.
7. Hiển thị thông báo thành công và cập nhật danh sách.
8. Tạo/cập nhật Excel của ngày tương ứng, báo trạng thái đồng bộ.

## Tính năng bắt buộc

| Mã | Yêu cầu | Điều kiện hoàn thành |
| --- | --- | --- |
| F01 | Camera bật/tắt | Thao tác nhiều lần, giải phóng thiết bị đúng |
| F02 | Nhận diện realtime | Có khung mặt và nhãn, nhận diện người đã đăng ký |
| F03 | Từ chối chưa xác định | Người lạ/ảnh chưa đạt điều kiện không được ghi |
| F04 | Đăng ký | ID, họ tên, ba ảnh hợp lệ, nhận diện được ngay sau lưu |
| F05 | Chống trùng | Một ID/ngày, còn hiệu lực sau khi mở lại app |
| F06 | Dữ liệu bền vững | Bản ghi đã xác nhận lưu còn sau khi khởi động lại |
| F07 | Excel tự động | File theo ngày, đủ cột, có thể thử lại khi bị khóa |
| F08 | Phản hồi UI | Trạng thái camera, đăng ký, điểm danh và Excel rõ ràng |
| F09 | Tích hợp | Frontend Next.js kết nối dịch vụ Python CV/backend, có hướng dẫn khởi chạy đầy đủ |
| F10 | Bàn giao | Hướng dẫn, bảng kết quả, báo cáo, slide, video |

Nhận diện từng người lần lượt là trường hợp demo chính. Pipeline xử lý các mặt riêng biệt và có bài thử hai người đồng thời. Quy mô đám đông sẽ cần đánh giá bổ sung.

## Tính năng tùy thời gian

- Tìm kiếm lịch sử.
- Chọn camera từ UI.
- Đăng ký lại hoặc vô hiệu hóa thành viên qua UI.
- Đóng gói executable sau khi bản Python đã ổn định.

## Hướng phát triển sau bản nộp

Liveness chuyên dụng, nhiều camera, đồng bộ cloud, tài khoản/phân quyền, nhiều phiên học mỗi ngày và triển khai vận hành dài hạn được ghi vào phần hướng phát triển của báo cáo.

## Dữ liệu cần ở từng thời điểm

| Thời điểm | Dữ liệu cần |
| --- | --- |
| Thiết kế và viết module | ID giả, tên giả, frame/sự kiện mô phỏng |
| Thử CV đầu tiên | Ảnh khác nhau của ít nhất hai người đã đồng ý tham gia |
| Đăng ký trong app | ID/MSSV dạng chuỗi, họ tên, ba ảnh webcam hợp lệ |
| Hiệu chỉnh | Lượt ảnh/video mới của người quen và người chưa đăng ký |
| Kiểm thử cuối | Lượt thử độc lập với dữ liệu đăng ký và hiệu chỉnh |
| Báo cáo nhóm | Họ tên và MSSV chính xác của bốn thành viên |

Họ tên, MSSV và ảnh thật được bổ sung khi đến công việc tương ứng. Mọi thành viên tham gia dùng cùng chức năng đăng ký, tránh hardcode tên vào nhận diện. ID có thể là MSSV hoặc mã thử nghiệm duy nhất. Chức năng này tạo hồ sơ nhận diện lưu tại backend; mọi browser trỏ cùng backend dùng chung dữ liệu.

## Trình tự triển khai đã được phê duyệt

- Chủ dự án đã duyệt dựng frontend trong frontend/ bằng Next.js App Router.
- UI tiếng Anh sử dụng authkit.com-DESIGN.md và các font thay thế được chỉ định trong mẫu.
- Hoàn thiện và kiểm tra UI trước, rồi triển khai CV và tích hợp.
- Giai đoạn frontend ban đầu đã kết thúc; adapter demo được thay bằng API thật. Không mang dữ liệu local mock sang DB.
- Ngưỡng matching, quality gate và thông số hiệu năng được hiệu chỉnh bằng dữ liệu thật trong quá trình phát triển.

## Hoàn thành phiên bản nộp

Mọi tính năng F01–F10 có bằng chứng kiểm tra, lỗi nghiêm trọng được xử lý, kết quả đo có số lượt cụ thể và bộ nộp chạy được trên máy demo. Mục tiêu độ chính xác/tốc độ trong TEST_PLAN là mục tiêu đánh giá, cần ghi kết quả đo trước khi tuyên bố đạt.
