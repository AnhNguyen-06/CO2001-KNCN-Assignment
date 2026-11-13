# Kế hoạch kiểm thử và đo lường

## Trạng thái

Bản FE–CV đã tích hợp. Kết quả tự động và phạm vi xác minh được ghi dưới đây; các bảng hiện trường còn chờ nhóm đăng ký và thử thật.

## Bổ sung deployment miễn phí

Đã kiểm tra 62/62 bài backend với PostgreSQL 17 thật trong Docker cùng các bài SQLite cũ. Sáu bài mới bao phủ embedding BYTEA/Unicode/ID số 0 đầu, restart, đăng ký rollback, 16 request điểm danh đồng thời, đổi ngày, revision và API CV→PostgreSQL→Excel download. Có một deprecation warning upstream Starlette/httpx như bản trước.

Docker Linux build thành công từ backend/Dockerfile, dùng OpenCV headless và model checksum cố định. Container giới hạn 0.1 CPU/512 MB chạy 8 frame probe khác ảnh đăng ký, processing_ms lần lượt 812.87,661.04,864.83,573.77,678.18,752.99,694.86,766.76. Đăng ký mất 4.53s, ghi đúng 1 attendance event và 1 record. Bộ nhớ quan sát sau lượt thử 184.6 MiB/512 MiB. Đây là mô phỏng tài nguyên local, cần đo mạng/CPU chia sẻ Render thực sau deploy.

Browser end-to-end trên Next production + Docker Linux 0.1 CPU/512 MB + PostgreSQL thật đạt 9/9 trong 2.8 phút. Gồm đăng ký qua native fake camera và model thật, liên tục 60s chỉ 1 bản ghi, người lạ/no-face, download workbook text-safe, persistence sau xóa localStorage, daily duplicate, camera/Excel/service errors, tự kết nối lại sau cold-start 503 và responsive. Database test riêng, không ghi vào DB local của nhóm.

TypeScript typecheck, Next production build, Ruff và Docker runtime dependency check được chạy theo hướng dẫn. Bản cloud chưa được deploy vào tài khoản Render/Neon của chủ dự án. Hướng dẫn và tiêu chí nghiệm thu ở DEPLOYMENT.

Hồi quy browser SQLite local cũng đạt 9/9 trong 2.2 phút, gồm cold start trả trang HTML và tự khôi phục. Đã restart container API và đối chiếu dữ liệu PostgreSQL sau khởi động lại. Các lượt này dùng database test riêng.

## Kết quả bản tích hợp FE–CV trước bổ sung cloud (lịch sử)

Môi trường Windows, Python 3.13, Node 24, Chrome/Playwright; actual YuNet/SFace ONNX. Backend suite: **56/56 pass**, gồm 8 API tests mới bên cạnh 48 baseline tests. Có một deprecation warning upstream từ Starlette TestClient/httpx, không ảnh hưởng runtime.

API tests kiểm tra DB trống, đăng ký tên Unicode/ID số 0 đầu, retry idempotent/conflict, no-face, ba ảnh khác danh tính, CV→commit→Excel, restart, người lạ, phiên dừng/hết hạn, hai browser tracker độc lập, payload limit, server key và hủy trong lúc inference.

Browser suite mới thay bộ test mock bằng 8 bài end-to-end với hai server riêng 8001/3100 và SQLite mới mỗi lượt. Chrome phát video portrait công khai qua native fake camera; CV không bị mock. Bao phủ đăng ký 3 mẫu, save/reload, actual check-in/overlay, media cleanup, localStorage clear vẫn giữ dữ liệu, daily duplicate, Excel thật (đọc workbook và đối chiếu ID/tên/status), kiểm tra trực tiếp SQLite counts 1 person / 3 samples / 1 attendance, legacy mock data không import, unknown/no-face, permission denied, service outage/retry, reset preferences và responsive 390px.

Kết quả browser cuối: **8/8 pass trong 1.8 phút**, gồm duy trì nhận diện liên tục 60 giây mà vẫn chỉ có 1 bản ghi, cùng phản hồi lỗi khi retry Excel mất kết nối. Screenshots ở frontend/test-results/. Đã xem ảnh desktop/mobile và overlay theo kết quả model. TypeScript typecheck và production build pass; npm audit báo 0 vulnerabilities ở lockfile hiện tại. Ảnh test công khai và DB test nằm trong backend/var, bị loại khỏi Git. DB ứng dụng thật đã xác minh 0 thành viên và 0 bản ghi, giữ trống cho chủ dự án.

Các phép thử này xác nhận chức năng bằng dữ liệu kiểm soát, không chứng minh độ chính xác bốn thành viên hoặc liveness. Chưa nhận ảnh nhóm; nhóm sẽ đăng ký trên web theo yêu cầu.

## Kết quả giai đoạn frontend trước tích hợp (lịch sử)

Frontend Next.js App Router đã được kiểm tra trên Windows, Node 24.12.0, npm 11.6.2, Google Chrome qua Playwright. Phiên bản dependencies chính được khóa trong frontend/package-lock.json.

| Kiểm tra | Kết quả |
| --- | --- |
| TypeScript typecheck | Pass |
| Next.js production build | Pass, sinh đầy đủ các route |
| Browser E2E | 8/8 pass |
| Landing desktop/mobile | Đã render và xem ảnh chụp, kiểm tra product fan, typography, circuit và closing choices |
| Workspace desktop/mobile | Đã xem ảnh chụp camera, đăng ký, members, records, settings |
| Demo check-in | Ghi mới, chống trùng sau reload và từ chối visitor mô phỏng đều pass |
| Đăng ký | Kiểm tra ID trùng, ba mẫu, review, lưu và reload profile đều pass |
| Excel download | Tải .xlsx từ browser, đọc lại nội dung workbook và đối chiếu view đã lọc |
| Camera preview | Synthetic webcam hiển thị được, chụp mẫu được, media tracks kết thúc khi tắt/đóng |
| Camera error | Permission denied có thông báo và nút retry |
| Preferences | Lưu sau reload, reduced motion và reset có xác nhận đều pass |
| Responsive | 1440px desktop và 390px mobile, các route mobile không tràn chiều ngang |
| Dependency audit | 0 vulnerabilities tại lần cài khóa hiện tại |

Chạy lại bằng hướng dẫn frontend/README.md. Bộ kiểm tra camera dùng thiết bị giả của Chrome để kiểm tra vòng đời API. Chất lượng webcam vật lý, độ chính xác nhận diện và độ trễ CV sẽ được đo trong giai đoạn CV. Các kết quả UI ở trên dùng dữ liệu demo local, với trạng thái frontend preview hiển thị trong workspace.

## Môi trường và dữ liệu

### Kết quả baseline CV

Baseline độc lập đã được triển khai trong backend/. Các bài kiểm tra bao phủ matching, quality, tracking, stale frames, thông báo sau commit, SQLite chống trùng, đồng thời, đổi ngày, rollback đăng ký và Excel phục hồi. Nhóm model test chạy ONNX thật cùng ảnh ví dụ và video, gồm một probe khác ảnh đăng ký, một người ngoài gallery và hai người cùng khung.

Kết quả gồm 48 bài tự động, model hashes đúng, pip check hợp lệ và Ruff pass. Webcam local đã mở được 1280×720 và chạy 20 frame. Bài smoke đo trung bình 48.69 ms/p95 60.77 ms cho suy luận 15 lượt ảnh, 706.46 ms từ frame đầu đến thông báo đã lưu. Nội dung, ngưỡng, nguồn dữ liệu và phạm vi phép đo được ghi tại [CV_BASELINE](CV_BASELINE.md).

Các số trên là xác minh baseline bằng dữ liệu ví dụ. Bộ đo hiện trường với sinh viên, ánh sáng, góc mặt, kính/mũ và ảnh điện thoại vẫn được thực hiện theo các phần bên dưới. Frontend end-to-end đã được nối và kiểm tra theo phần bản tích hợp bên trên.

Ghi CPU, RAM, hệ điều hành, webcam, độ phân giải, khoảng cách, ánh sáng, phiên bản Python/thư viện, model checksum và config. Các bài so sánh dùng cùng điều kiện đã ghi.

- Enrollment gồm ba ảnh/người để tạo gallery.
- Calibration gồm ảnh/lượt mới để chọn threshold, margin, quality và temporal settings.
- Final test gồm các lượt chưa dùng trong hai nhóm trên.
- Giữ một số người ngoài gallery để kiểm tra unknown.
- Mỗi lượt là một lần người bước vào và rời vùng nhận diện. Reset điều kiện trước lượt mới.
- Người đã điểm danh vẫn có thể thử kết quả nhận diện. Kết quả lưu expected là already_exists trong cùng ngày.
- Nếu có 5–10 người ngoài nhóm, thống nhất trước ai được đăng ký và ai giữ ngoài gallery. Ghi cả số người và số lượt cho từng nhóm.

## Kiểm thử chức năng

| ID | Tình huống | Kết quả mong đợi |
| --- | --- | --- |
| C01 | Mở app với gallery trống | Hướng dẫn đăng ký, UI hoạt động |
| C02 | Bật/tắt camera nhiều lần | Thiết bị giải phóng, UI phản hồi, kết quả cũ bị bỏ |
| C03 | Camera bị app khác chiếm hoặc mất thiết bị | Lỗi có thể hiểu, thử lại được |
| C04 | Người đã đăng ký xuất hiện | Đúng ID, xác nhận, lưu một hàng |
| C05 | Người lạ xuất hiện | Unknown, không tạo bản ghi |
| C06 | Người đứng yên một phút | Một hàng điểm danh |
| C07 | Rời đi rồi quay lại cùng ngày | already_exists, giờ gốc giữ đúng |
| C08 | Đóng/mở app trong ngày | Chống trùng còn hiệu lực |
| C09 | Đổi ngày bằng clock thử | Cho một bản ghi ngày mới và file tương ứng |
| C10 | Đăng ký người mới | Ba mẫu hợp lệ, nhận diện được sau reload |
| C11 | ID trùng/tên trống/mẫu lỗi | Validation rõ, dữ liệu nhất quán |
| C12 | Hủy/chụp lại đăng ký | Mẫu tạm được xử lý đúng, mode điểm danh trở lại |
| C13 | Hai người trong khung, đổi vị trí | Mỗi mặt gắn đúng bằng chứng, không trộn ID |
| C14 | Excel đang mở và khóa file | Điểm danh vẫn lưu, xuất báo chờ thử lại |
| C15 | Đóng Excel rồi thử xuất | File đầy đủ, không trùng hàng |
| C16 | SQLite ghi lỗi | Báo chưa lưu, không có thông báo thành công |
| C17 | Ngừng app trước xuất/mở lại | Revision pending được phát hiện, xuất bù |
| C18 | Thêm bản ghi trong khi export | File cuối chứa dữ liệu mới, revision còn pending đến khi đủ |
| C19 | Tên tiếng Việt, tên dài, ID số 0 đầu | UI/SQLite/Excel giữ đúng |
| C20 | ID/tên bắt đầu bằng ký tự công thức | Excel chứa text an toàn |
| C21 | Model thiếu/sai file/gallery sai metadata | Hướng dẫn lỗi, ngừng nhận diện đến khi dữ liệu hợp lệ |
| C22 | Chạy 15–30 phút | Camera/UI hoạt động, không có backlog frame tăng liên tục |
| C23 | Tắt camera/đổi mode lúc CV đang chạy | Kết quả lỗi thời không tạo yêu cầu mới |
| C24 | Hai request cùng ID/ngày đồng thời | Một created, một already_exists |
| C25 | Lưu đăng ký lỗi giữa chừng | Transaction rollback, không có hồ sơ thiếu mẫu |
| C26 | Cài trên máy thứ hai | Theo README chạy được, font hiển thị đúng |

Logic unique constraint, clock đổi ngày, rollback đăng ký, export revision và text Excel phù hợp kiểm tra tự động. Webcam, ánh sáng, UI và mẫu thiết kế phù hợp kiểm tra thủ công. Chọn bài tự động để bảo vệ hành vi có rủi ro thực tế.

## Ma trận điều kiện CV

| Điều kiện | Nội dung ghi nhận |
| --- | --- |
| Ánh sáng tốt, chính diện | Baseline nhận đúng và độ trễ |
| Thiếu sáng | Mức nhận đúng/từ chối, phản hồi quality |
| Quay 30–45 độ | Mức nhận đúng, thất bại và độ trễ |
| Kính/mũ | Kết quả theo loại che khuất |
| Hai mặt | Từng ID, thời điểm xác nhận, liên kết track |
| Người chưa đăng ký | Unknown hoặc nhầm ID nào |
| Ảnh trên điện thoại | Có bị chấp nhận hay không, điều kiện thử |

Ảnh điện thoại dùng để đánh giá giới hạn giả mạo. Nếu ứng dụng chấp nhận ảnh, báo cáo mô tả đúng kết quả và hướng cải tiến liveness.

## Định nghĩa chỉ số

Với mỗi lượt của người đã đăng ký, ghi quyết định đầu tiên trong thời gian quan sát đã chọn. Phân loại đúng ID, sai ID hoặc chưa xác định/timeout. Người lạ ghi bị chấp nhận thành ID nào hoặc từ chối. Ghi thêm mọi lần chấp nhận sai xảy ra về sau trong lượt để tránh bỏ sót lỗi sau quyết định đầu tiên.

| Chỉ số | Công thức/cách ghi |
| --- | --- |
| Nhận đúng | Lượt người đã đăng ký có quyết định đầu đúng / tổng lượt nhóm đó |
| Sai danh tính | Lượt người đã đăng ký có quyết định đầu sai ID / tổng lượt nhóm đó |
| Không nhận ra | Lượt người đã đăng ký bị unknown hoặc timeout / tổng lượt nhóm đó |
| Chấp nhận người lạ | Lượt người lạ có ít nhất một lần được chấp nhận / tổng lượt người lạ |
| Độ trễ danh tính | Từ lúc mặt đủ điều kiện quan sát đến CONFIRMED, đo bằng monotonic |
| Độ trễ điểm danh | Từ cùng mốc đến UI nhận kết quả commit |
| Hiệu năng | FPS preview và tần suất inference đo riêng |

Đề xuất timeout quan sát ban đầu là 5 giây, cần chốt trước final test. Báo cáo latency trung bình và p95 cho các lượt thành công, kèm số timeout/thất bại. Ghi rõ mốc đầu do người thử đánh dấu hay quality gate tự xác định.

## Mục tiêu đánh giá

- Ánh sáng tốt hướng tới nhận đúng ít nhất 95% trong tập thử của nhóm.
- Hướng tới xác định danh tính trong khoảng một giây và báo cả độ trễ commit.
- Mục tiêu người lạ là 0 lượt bị chấp nhận trong final test, báo cả tử số/mẫu số.
- Chống trùng đạt toàn bộ C06–C09 và C24.
- Dữ liệu đã commit còn nguyên khi retry export hoặc mở lại app.
- Hoàn tất kiểm tra cài sạch, UI theo mẫu và thử liên tục.

Các mục tiêu cần kết quả đo để xác nhận. Tập thử nhỏ được trình bày đúng phạm vi, ví dụ 0/20 lượt chấp nhận người lạ.

## Mẫu ghi kết quả

| Lượt | Điều kiện | ID thật hoặc unknown | Quyết định đầu | Có chấp nhận sai về sau | Latency nhận diện | Latency commit | Kết quả lưu | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chờ chạy | | | | | | | | |

| Test ID | Build/config | Pass/Fail | Bằng chứng | Người kiểm tra | Lỗi liên quan |
| --- | --- | --- | --- | --- | --- |
| Chờ chạy | | | | | |

Nếu điều chỉnh ngưỡng sau final test, ghi cấu hình mới và chạy final test mới. Giữ dữ liệu kết quả cũ để giải thích quá trình cải tiến.
