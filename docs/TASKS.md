# Phân công và kế hoạch bốn ngày

## Trạng thái sau tích hợp

Frontend và baseline CV đã kết nối qua FastAPI + Next proxy. Đã có đăng ký 3 ảnh thật, gallery refresh, CV realtime theo phiên browser, SQLite bền vững, chống trùng và Excel tự động/tải theo bộ lọc. Adapter mock và hồ sơ seed đã bỏ.

| Thành viên | Việc tiếp theo | Bằng chứng cần |
| --- | --- | --- |
| Quang Anh | Đăng ký đầu tiên, kiểm tra webcam vật lý và UI, đánh giá ngưỡng với nhóm | Đi hết WEB_DEMO và ghi lỗi tái hiện nếu có |
| Lâm | Đối chiếu DB/Excel sau lượt nhóm, thử khóa Excel/retry, hỗ trợ persistent host | ID/tên/giờ khớp, restart không trùng |
| Ân | Điều phối1–2 người đăng ký trước và 1–2 người đăng ký trên lớp; đo field tests | Bảng số lượt/đúng/nhầm/từ chối/latency |
| Hoàng | Cài máy thứ hai, chuẩn bị host, cập nhật báo cáo/slide/video | Hướng dẫn chạy đã thử, chỉ dùng số liệu đã đo |

Chủ dự án sẽ gửi GitHub remote sau khi kiểm tra; hiện chưa push hoặc deploy. Bảng bốn ngày bên dưới giữ kế hoạch và phân công gốc, không thay cho xác nhận hoàn thành các đầu việc báo cáo/hiện trường.

## Trách nhiệm và ranh giới

Baseline CV độc lập hiện có YuNet/SFace, đăng ký, quality/alignment, matching, temporal confirmation, SQLite, thông báo và Excel. Đã xác minh bằng model thật, video và camera local. Adapter web đã hoàn thành; việc tiếp theo là dữ liệu hiện trường và triển khai, giữ phân công CV/UI cho Quang Anh, dữ liệu cho Lâm, đăng ký/QA cho Ân và tài liệu/môi trường cho Hoàng.

| Thành viên | Sở hữu | Phối hợp |
| --- | --- | --- |
| Chủ dự án | Model, camera, matching, temporal confirmation, UI, controller | Chốt hợp đồng với Lâm/Ân, giải thích CV cho Hoàng |
| Lâm | Repository, attendance service, Excel exporter | Nhận sự kiện danh tính, cấp API lưu mẫu cho Ân |
| Ân | Registration service, chuẩn bị dữ liệu, test hiện trường | Dùng CV API của chủ dự án, lưu qua repository của Lâm |
| Hoàng | Môi trường, README cài đặt, báo cáo, slide, video, bộ nộp | Nhận mô tả module và số liệu từ ba người còn lại |

Kế hoạch giả định mỗi người có khoảng 6–8 giờ tập trung/ngày. UI hoàn thiện phụ thuộc mẫu/font/MCP chủ dự án cung cấp. Nếu mẫu đến muộn, tiếp tục phần lõi và dùng thời gian UI còn lại cho các màn hình bắt buộc.

## Danh sách việc

| ID | Chủ sở hữu | Đầu việc | Phụ thuộc | Điều kiện hoàn thành | Ngày |
| --- | --- | --- | --- | --- | --- |
| T01 | Hoàng | Repo, môi trường và hướng dẫn ban đầu | Duyệt triển khai | Tạo môi trường và xác minh imports trên Windows | 1 |
| T02 | Chủ dự án | Chạy YuNet + SFace trên ảnh tĩnh | T01, ảnh thử tự nguyện | In tên/unknown đúng trên các ảnh khác nhau | 1 |
| T03 | Chủ dự án | Camera và pipeline realtime | T02 | Preview, khung mặt, tên, bật/tắt ổn định | 1 |
| T04 | Lâm | Schema, repository, clock, chống trùng | INTERFACES | Ghi mới/đã tồn tại/lỗi rõ, mở lại còn dữ liệu | 1 |
| T05 | Lâm | Xuất Excel từ database | T04 | Đúng cột, ID dạng text, file ngày, retry | 1–2 |
| T06 | Ân | Quy trình thông tin và ba mẫu đăng ký | INTERFACES | Logic chạy với CV giả, validation và hủy hoạt động | 1 |
| T07 | Ân | Thu dữ liệu và chuẩn bị test cases | Người tham gia đồng ý | Có tập đăng ký/hiệu chỉnh/test tách biệt | 1–2 |
| T08 | Chủ dự án | Tích hợp nhận diện → lưu → phản hồi | T03, T04 | Một lượt điểm danh xuyên suốt | 1 |
| T09 | Chủ dự án | Tiếp nhận mẫu và dựng UI | Mẫu/font/MCP, UI_SPEC | UI chức năng theo mẫu, đủ trạng thái | 2–3 |
| T10 | Ân | Nối đăng ký thật và refresh gallery | T02, T04, T06 | Thêm người mới và nhận diện ngay | 2 |
| T11 | Chủ dự án | Controller, queue, confirmation theo mặt | T03, T08 | UI phản hồi, loại kết quả cũ, hai mặt riêng | 2 |
| T12 | Lâm | Revision Excel và phục hồi | T04, T05 | Khóa file/mở lại vẫn xuất bù được | 2 |
| T13 | Hoàng | Cài sạch trên máy thứ hai | T01, bản tích hợp | Ghi phiên bản, nguồn/checksum model, chạy được | 2–3 |
| T14 | Ân | Chạy test chức năng và hiện trường | T07, T10, T11, T12 | Bảng lượt thử, latency, nhầm/từ chối, lỗi | 3 |
| T15 | Chủ dự án | Hiệu chỉnh và sửa CV/UI | T14 | Ngưỡng được lưu, sửa lỗi có tái kiểm tra | 3 |
| T16 | Lâm | Sửa dữ liệu/Excel | T14 | Các lỗi mất dữ liệu/trùng/xuất được xử lý | 3 |
| T17 | Hoàng | Báo cáo, slides, video nháp | Mô tả module, T14 | Bản nháp dùng số liệu thật | 1–3 |
| T18 | Cả nhóm | Regression và diễn tập | Bản freeze | Đi hết demo, lỗi nghiêm trọng được đóng | 4 |
| T19 | Hoàng | Bộ nộp cuối | T13, T17, T18 | Mã nguồn, hướng dẫn, báo cáo, slides, video | 4 |

## Mốc từng ngày

| Ngày | Điều kiện kết thúc |
| --- | --- |
| 1 | Model chạy thật, có điểm danh xuyên suốt tối thiểu, các module còn lại chạy với dữ liệu giả |
| 2 | Đăng ký → nhận diện → lưu → mở lại chống trùng → Excel hoạt động |
| 3 | Có số liệu thử, ngưỡng/config cuối, UI theo mẫu nếu đã nhận, freeze tính năng |
| 4 | Hoàn tất regression, cài sạch, diễn tập và bộ nộp |

## Công việc có thể làm song song

- Lâm dùng request giả để hoàn thành database/Excel trước camera thật.
- Ân dùng mẫu embedding giả có schema hợp lệ để làm registration service.
- Chủ dự án dựng UI qua sự kiện giả sau khi nhận mẫu.
- Hoàng viết cấu trúc báo cáo và hướng dẫn ngay ngày đầu, điền số liệu sau khi Ân đo.

## Tích hợp và bàn giao trong nhóm

Mỗi đầu việc gửi commit/nhánh, mô tả hành vi, hướng dẫn thử và kết quả đã kiểm tra. Tích hợp bản chạy được cuối mỗi ngày. Lỗi ghi vào bảng có bước tái hiện, mức ảnh hưởng, chủ sở hữu và kết quả tái kiểm tra.

| Mức lỗi | Cách xử lý |
| --- | --- |
| Nghiêm trọng | Mất dữ liệu, ghi nhầm ID, treo app, không chạy được trên máy demo. Xử lý trước bàn giao |
| Ảnh hưởng chức năng | Đăng ký/Excel/camera lỗi ở trường hợp hỗ trợ. Ưu tiên trong ngày 3 |
| Thẩm mỹ nhỏ | Xử lý sau các lỗi chức năng theo thời gian còn lại |

## Điểm điều chỉnh

Sau 2–3 giờ đầu ngày 1 xác minh cặp model/runtime trên máy demo. Nếu gặp trở ngại, ghi lỗi cụ thể trước khi đổi phương án. Khi đổi phải cập nhật DECISIONS và các hợp đồng bị ảnh hưởng.

Từ cuối ngày 3 chỉ thêm công việc cần cho sửa lỗi hoặc bộ nộp. Các ý tưởng mới chuyển sang hướng phát triển sau. Bảng này là kế hoạch, trạng thái thực hiện và thời gian thực tế sẽ được cập nhật khi bắt đầu triển khai.
