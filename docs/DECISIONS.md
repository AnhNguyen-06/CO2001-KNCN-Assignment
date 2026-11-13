# Quyết định kỹ thuật

Ngày lập 13/11/2026. Các lựa chọn đã được chủ dự án đồng ý ở mức kế hoạch. Việc xác minh runtime, dependencies, hiệu năng và UI diễn ra khi triển khai.

## D01 — Pretrained local

Dùng model đã huấn luyện để tạo embedding. Đăng ký tạo ba mẫu gắn ID, nhận diện dùng so khớp cosine. Quy trình này phù hợp bốn ngày và nhu cầu thêm người từ giao diện. Model inference chạy local trên CPU.

## D02 — YuNet và SFace qua OpenCV

Cặp thử đầu tiên là `face_detection_yunet_2023mar.onnx` và `face_recognition_sface_2021dec.onnx` với OpenCV 4.x tương thích. OpenCV có FaceDetectorYN và FaceRecognizerSF cho pipeline phát hiện, căn chỉnh và nhận diện. Pin phiên bản đã chạy thành công cùng checksum model.

YuNet trong OpenCV Zoo ghi giấy phép MIT, SFace ghi Apache 2.0. Khi lấy model cần lưu nguồn và thông tin giấy phép đi kèm. Tài liệu YuNet phân biệt model 2023 và bản dynamic-input mới, nên chọn đúng cặp runtime/model.

- [Hướng dẫn OpenCV](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html)
- [YuNet README](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md)
- [SFace README](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)

## D03 — Phương án dự phòng model

InsightFace buffalo_sc là lựa chọn để đánh giá khi cặp chính gặp vấn đề cụ thể. Model zoo công bố gói này gồm SCRFD-500MF và MobileFaceNet, khoảng 16 MB. Phải xem giấy phép weights và xác minh khả năng cài/chạy trước khi quyết định đổi. Thay đổi model kéo theo tái tạo gallery embedding.

Thư viện face_recognition/dlib có thể dùng nếu môi trường đã ổn. Repository chính thức ghi Windows chưa được hỗ trợ chính thức, nên ưu tiên giảm rủi ro cài đặt trong lịch bốn ngày.

- [InsightFace model zoo](https://github.com/deepinsight/insightface/tree/master/model_zoo)
- [InsightFace license](https://github.com/deepinsight/insightface#license)
- [face_recognition](https://github.com/ageitgey/face_recognition)

## D04 — Desktop UI và mẫu thiết kế

CustomTkinter + Pillow là phương án UI ban đầu. Chủ dự án cung cấp mẫu design, font và MCP sau khi lựa chọn. Khi tiếp nhận mẫu sẽ cập nhật UI_SPEC, xác minh yêu cầu trên framework và trình bày thay đổi cần thiết nếu có.

- [CustomTkinter documentation](https://customtkinter.tomschimansky.com/documentation/)

### Quyết định thay thế theo phê duyệt mới

Chủ dự án chọn frontend web bằng Next.js kết hợp router và cung cấp `authkit.com-DESIGN.md`. Triển khai Next.js App Router, React và TypeScript trong `frontend/`, giao diện tiếng Anh. Dùng Inter và Manrope theo font thay thế trong design guide, đóng gói font local. Tên làm việc được chọn cho UI là Presence. Luồng công việc chuyển thành frontend → CV → tích hợp. Thư viện UI desktop trong quyết định ban đầu được thay bằng frontend web.

UI phase dùng localStorage cho metadata/demo records và camera trình duyệt cho preview. Nhận diện được mô phỏng có nhãn demo, Excel tải từ dữ liệu demo đã lọc. Giai đoạn này đã kết thúc; API thật và SQLite thay adapter local theo D11.

## D05 — SQLite và Excel

SQLite giữ dữ liệu chính cùng constraint chống trùng. openpyxl dựng Excel từ dữ liệu theo ngày. Cách tổ chức này cho phép phục hồi và thử xuất lại khi file bị khóa. Revision dữ liệu và revision xuất xác định phần còn chờ đồng bộ.

## D06 — Một ID mỗi ngày

Ngày điểm danh tính theo Asia/Ho_Chi_Minh. Bản đầu lưu trạng thái Present và giờ đầu tiên thành công của ngày. Nhu cầu nhiều phiên học có thể bổ sung session_id ở phiên bản sau.

## D07 — Xác nhận và hiệu chỉnh

Ba embedding mỗi ID, điểm ID dùng cosine lớn nhất. Ngưỡng tuyệt đối, margin giữa hai ID và xác nhận qua nhiều lần xử lý được hiệu chỉnh trên dữ liệu riêng. Các quyết định này cần báo config và kết quả final test. Similarity hiển thị đúng đơn vị nếu sử dụng trong nghiên cứu.

## D08 — Đánh giá giả mạo

Thực hiện thử ảnh điện thoại và công bố kết quả. Hướng phát triển liveness cần pipeline và đánh giá riêng. Xác nhận nhiều frame phục vụ ổn định nhận diện.

## D09 — Dữ liệu và thời điểm cung cấp

Viết phần lõi bằng dữ liệu giả có schema thống nhất. Hồ sơ thật được tạo khi đăng ký bằng ID/MSSV, họ tên và ảnh webcam. Họ tên/MSSV nhóm cho báo cáo có thể bổ sung sau. Kiểm thử CV thật cần ảnh/lượt mới của người đã đồng ý tham gia.

## D10 — Baseline CV độc lập trước tích hợp

Đã triển khai Python package trong backend/ và khóa môi trường Python 3.13, OpenCV 4.14.0, NumPy 2.5.4, openpyxl 3.1.5. Tiếp tục dùng cặp YuNet 2023mar và SFace 2021dec đã pin checksum. Bộ model thật đã qua bài smoke với ảnh probe khác ảnh đăng ký, người ngoài gallery, hai mặt và video CLI. Webcam local cũng chạy được ở 1280×720.

Ngưỡng khởi đầu gồm cosine 0.45, margin 0.08, ba quan sát và thời lượng tối thiểu 0.35 giây. Chất lượng được kiểm tra trên độ lớn mặt, visibility, landmark geometry, exposure và sharpness crop đã căn chỉnh. Các số này là cấu hình baseline cần hiệu chỉnh với dữ liệu nhóm.

Điểm nối cho frontend là BaselineSession. Bước tích hợp sẽ quyết định giao thức web và timestamp backend, giữ model và lưu trữ ở Python. Các kết quả hiện tại đủ để tiếp tục baseline YuNet + SFace theo kế hoạch của chủ dự án.

## Những điểm còn cần xác minh

| Hạng mục | Thời điểm | Phụ trách |
| --- | --- | --- |
| Mẫu UI/font/MCP | Khi chủ dự án lựa chọn | Chủ dự án |
| Máy demo, webcam, cấu hình | Đầu ngày 1 | Chủ dự án + Hoàng |
| Python 3.13 và thư viện cụ thể | Đã khóa; thử máy thứ hai | Hoàng |
| Nguồn tải, checksum, giấy phép model đã lấy | Ngày 1 | Hoàng + chủ dự án |
| Threshold, margin, quality, temporal config | Ngày 3 | Chủ dự án + Ân |
| Latency/độ chính xác thực tế | Ngày 3 | Ân |
| Font và cài sạch máy thứ hai | Ngày 2–4 | Hoàng |
| Deadline nộp chính xác | Khi nhóm chốt lịch | Chủ dự án |

## Lịch sử thay đổi

| Ngày | Thay đổi | Cơ sở |
| --- | --- | --- |
| 2026-11-13 | Lập bộ tài liệu thiết kế ban đầu | Plan được chủ dự án đồng ý, bổ sung yêu cầu chờ mẫu UI/font/MCP |

## D11 — Web integration và nguồn dữ liệu thật

Thay local demo adapter bằng FastAPI, same-origin Next route proxy và SQLite. Browser sở hữu webcam, gửi JPEG tuần tự; backend cấp timestamp và lease. Model dùng chung một inference thread, tracker độc lập từng browser, exporter nền dùng chung. Chỉ CV được tạo attendance; client không gửi ID để giả lập check-in.

Đăng ký yêu cầu ID, họ tên và 3 ảnh thực, revalidate khi Save và lưu transaction. Ảnh gốc không lưu, chỉ embedding 128D và metadata. Retry cùng nội dung idempotent. Website không seed tài khoản/điểm danh. Nhóm sẽ đăng ký trực tiếp; các test dùng DB riêng.

## D12 — Deploy tách frontend và persistent backend

Vercel chạy Next frontend/proxy. Python chạy ở host có HTTPS và persistent volume cho SQLite/Excel, một worker. PRESENCE_BACKEND_URL và PRESENCE_BACKEND_KEY chỉ ở Next server; PRESENCE_DATA_DIR và cùng key ở Python service. Chưa triển khai remote.

Bản này tạo hồ sơ nhận diện thực, chưa có password login/phân quyền hay liveness. Không coi backend key là xác thực từng người dùng. Xem [DEPLOYMENT](DEPLOYMENT.md).

## D13 — Hosting miễn phí theo yêu cầu chủ dự án

Chọn Vercel Hobby + Render Free + Neon Free. Bổ sung psycopg PostgreSQL bên cạnh SQLite local. DATABASE_URL chỉ đặt ở backend. Giữ ID chuỗi, embedding float32, transaction, unique ID/ngày và dữ liệu cũ của local.

Render Free dùng filesystem tạm nên cloud export_mode=download dựng workbook từ DB trong bộ nhớ. Docker dùng OpenCV headless, một inference thread, model tải lúc build và process đọc PORT. Next proxy chuẩn hóa lỗi cold start; provider serialize workspace requests và tự thử lại.

Cloud configuration và hướng dẫn ở DEPLOYMENT. Kết quả test được ghi vào TEST_PLAN, cần thử endpoint Render/Neon thực sau khi chủ dự án tạo dịch vụ.
