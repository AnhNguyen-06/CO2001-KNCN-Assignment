# Baseline CV độc lập

## Hiện trạng

Baseline được triển khai trong backend/ theo thứ tự YuNet → kiểm tra chất lượng → căn chỉnh → SFace → matching → xác nhận theo từng mặt → SQLite → thông báo và Excel. Hướng dẫn cài/chạy nằm trong [backend/README](../backend/README.md). Frontend tiếp tục dùng adapter demo trong giai đoạn chuẩn bị tích hợp.

## Thành phần đã triển khai

| Module | Trách nhiệm |
| --- | --- |
| presence_cv/models.py | Tải model theo revision và xác minh kích thước/SHA-256 |
| presence_cv/vision.py | Resize detector, trả tọa độ gốc, quality gate, alignCrop, embedding, matching |
| presence_cv/tracking.py | Liên kết mặt bảo thủ và xác nhận nhiều quan sát |
| presence_cv/storage.py | Đăng ký nguyên tử, metadata embedding, chống trùng, revision Excel |
| presence_cv/export.py | Worker xuất ngày, file tạm, atomic replace, lock và phục hồi |
| presence_cv/session.py | Điều phối pipeline, stale/generation, thông báo sau commit |
| presence_cv/camera.py | Một chủ sở hữu webcam, buffer frame mới nhất, đóng thiết bị |
| presence_cv/display.py | Khung mặt, landmark, tên Unicode và thông báo trên preview |
| presence_cv/cli.py | Setup, doctor, register, inspect, run, records, members, export |

## Quy tắc vận hành

- Đăng ký ba ảnh khác nhau, mỗi ảnh đúng một mặt đạt chất lượng. Người và ba embedding được lưu trong một transaction.
- Gallery có metadata model/preprocessing rõ ràng. Model khác cần gallery được đăng ký lại trong thư mục dữ liệu phù hợp.
- Điểm ID là cosine lớn nhất trong ba mẫu. Ngưỡng ban đầu 0.45, margin giữa hai ID là 0.08.
- Xác nhận cần ít nhất ba quan sát trong cửa sổ 1.5 giây và kéo dài tối thiểu 0.35 giây.
- Mất mặt, ảnh không đạt, thay ứng viên, tracking mơ hồ hoặc generation cũ đều làm mất bằng chứng xác nhận.
- SQLite áp dụng UNIQUE(person_id, attendance_date), ngày tính theo Asia/Ho_Chi_Minh.
- Thông báo thành công được phát sau commit, giữ nguyên giờ điểm danh đầu tiên.
- Excel tự cập nhật theo ngày ở worker riêng. Lỗi khóa file giữ bản ghi SQLite và cho thử xuất lại.
- Revision ngày được tăng trong giao dịch điểm danh. Startup tiếp tục xuất các ngày pending hoặc mất file.
- Dữ liệu thật, embedding, trọng số model và output thử được loại khỏi Git bằng .gitignore.

## Xác minh thực tế

Môi trường đã chạy gồm Windows, Python 3.13.5, OpenCV 4.14.0, NumPy 2.5.4 và openpyxl 3.1.5. Requirements được khóa trong [requirements.lock.txt](../backend/requirements.lock.txt).

Hai model có SHA-256 đã đối chiếu với metadata OpenCV Zoo. Nhận diện trên ảnh probe khác ảnh đăng ký cho kết quả đúng ID A, cosine khoảng 0.760 và runner-up khoảng 0.255. Người ngoài gallery có cosine tốt nhất khoảng 0.148 và được từ chối với threshold 0.45.

Bài smoke dùng ảnh ví dụ công khai, hai danh tính đã đăng ký, một danh tính giữ ngoài gallery và một ảnh có hai người. Mẫu đăng ký biến đổi từ cùng một ảnh gốc để kiểm tra cơ chế. Ảnh probe danh tính A là ảnh khác. Các chỉ số này phục vụ xác minh chức năng, cần bổ sung phép đo thực địa với sinh viên để đánh giá độ chính xác của bài tập.

Webcam thực tế đã mở được ở 1280×720, chạy 20 frame trực tiếp và kết thúc bình thường. Bài kiểm tra video dùng model thật đã phát thông báo attendance_created, lưu SQLite và phát excel_synced.

| Kiểm tra | Kết quả |
| --- | --- |
| Bộ kiểm thử tự động | 48 bài gồm logic, model thật, video CLI, ghi đồng thời, ngày mới, rollback và Excel |
| Nhận diện ảnh probe khác ảnh đăng ký | ID A, cosine khoảng 0.760 |
| Người giữ ngoài gallery | Unknown, cosine tốt nhất khoảng 0.148 |
| Hai người trong cùng ảnh | Hai ID riêng, hai bản ghi sau xác nhận |
| Suy luận sau warm-up, 15 lượt ảnh | Trung bình 48.69 ms, p95 60.77 ms |
| Frame đầu → thông báo sau commit | 706.46 ms trong luồng smoke lặp ảnh probe |
| Excel | Đọc lại workbook đúng cột, ID có số 0 đầu và tên Unicode |
| Khóa file thật trên Windows | Xuất thất bại có kiểm soát, lưu SQLite còn nguyên, thử lại thành công |
| Webcam local | Frame 1280×720, xử lý 20 frame, đóng bình thường |
| Kiểm tra môi trường/mã nguồn | pip check và Ruff |

Latency ở đây gồm các bước trong bài smoke local. Tốc độ còn phụ thuộc máy, độ phân giải và số mặt. Phần webcam trực tiếp xác minh capture/inference/vòng đời thiết bị với gallery trống. Điểm danh thật của nhóm cần đăng ký và thử riêng. Ảnh annotation của probe đã được render và xem để kiểm tra khung mặt, landmark và nhãn.

## Bằng chứng tự tái hiện

- `python main.py doctor` kiểm tra runtime, model và dữ liệu.
- `python main.py doctor --camera` kiểm tra frame webcam.
- `python -m tools.verification_data` tải fixture từ revision cố định.
- `python -m tools.verify_baseline` tạo báo cáo và workbook thử trong var/verification.
- `python -m pytest -q` chạy bộ kiểm tra logic và model thật khi đã có fixture.
- `python -m ruff check presence_cv tools tests` kiểm tra lỗi mã nguồn cơ bản.
- `python -m pip check` kiểm tra tương thích dependencies.

Các lệnh chạy từ backend với môi trường đã kích hoạt hoặc prefix .venv/Scripts/python.exe theo README. Báo cáo runtime đầy đủ nằm trong backend/var/verification/report.json và nguồn ảnh trong sources.json cùng thư mục.

## Tiêu chí trước khi tích hợp

Phần CV độc lập cần giữ đúng những hành vi đã kiểm tra khi nối web. Browser sẽ truyền ảnh cho một inference worker. Timestamp freshness phải lấy ở backend khi tiếp nhận, cùng clock domain với quá trình xử lý. Session generation, ID frame và reload gallery phải được nối với vòng đời camera/đăng ký của frontend.

Frontend đã nối FastAPI qua HTTP và Next.js proxy, nhận kết quả đã commit cùng trạng thái Excel riêng, đọc danh sách từ SQLite và tải workbook do backend tạo. BaselineSession là điểm nối; timestamp do backend cấp, mỗi browser có tracker/lease riêng. Hợp đồng hiện tại tại INTERFACES, hướng dẫn tại WEB_DEMO.

Nhóm tiếp tục đăng ký ba ảnh thật/người, hiệu chỉnh quality/matching/confirmation theo dữ liệu nhóm và đo tỷ lệ đúng/sai cùng latency. Thử ảnh điện thoại được ghi kết quả trong báo cáo. YuNet + SFace hiện đã đáp ứng các bài smoke của baseline, tiếp tục dùng cặp model này.

## Nguồn model và dữ liệu thử

- [OpenCV DNN Face Detection and Recognition](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html)
- [YuNet model và giấy phép](https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet)
- [SFace model và giấy phép](https://github.com/opencv/opencv_zoo/tree/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface)
- [Public example fixtures tại revision cố định](https://github.com/ageitgey/face_recognition/tree/9f3061aaeed9a8756d2c970f5dfe066617a8281d/examples)
