# Quy tắc nghiệp vụ và phát triển

## Danh tính và thời gian

| Mã | Quy tắc |
| --- | --- |
| R01 | person_id là chuỗi duy nhất. Giữ số 0 đầu, loại khoảng trắng đầu/cuối. Bản đầu so sánh ID sau trim, có phân biệt hoa/thường. MSSV nên dùng chữ số theo dữ liệu nhập. |
| R02 | full_name giữ dấu tiếng Việt và cách viết người dùng xác nhận. Chỉ trim hai đầu và yêu cầu có nội dung. |
| R03 | Tên trùng được phép. Mọi liên kết và chống trùng dùng person_id. |
| R04 | Một ID được lưu một bản ghi trong mỗi ngày theo Asia/Ho_Chi_Minh. UNIQUE(person_id, attendance_date) bảo vệ ở database. |
| R05 | Attendance service lấy thời gian hệ thống khi xử lý yêu cầu hợp lệ và suy ra ngày từ cùng timestamp. Timestamp lưu có timezone, Excel hiển thị giờ local. |
| R06 | Đồng hồ monotonic dùng đo độ trễ và hạn lịch sử CV. Đồng hồ lịch dùng ngày giờ điểm danh. |
| R07 | Lần nhận diện tiếp theo trong cùng ngày trả bản ghi đã tồn tại. Tên và giờ gốc của hàng điểm danh được giữ để đối chiếu. |

Ứng dụng dựa vào đồng hồ máy demo. Kiểm tra giờ và timezone trước demo. Bài thử qua nửa đêm dùng clock thay thế trong kiểm thử logic.

## Nhận diện

- Chỉ danh tính đang hoạt động và có mẫu tương thích model mới được dùng trong gallery.
- Registration và recognition dùng cùng pipeline alignment, màu ảnh, chuẩn hóa và model metadata.
- Dùng ba mẫu/người cho bản đầu. Điểm ID là cosine lớn nhất giữa probe và ba mẫu của ID đó.
- Ngưỡng tuyệt đối và margin giữa hai ID được chọn trên tập hiệu chỉnh. Thông số phải ghi vào cấu hình và kết quả thử.
- Gallery một ID chỉ kiểm tra ngưỡng tuyệt đối. Gallery trống hiển thị hướng dẫn đăng ký.
- Người lạ, điểm thấp, hai ứng viên gần nhau hoặc ảnh chưa đạt được hiển thị trạng thái tương ứng.
- Bằng chứng xác nhận thuộc từng mặt đang theo dõi. Reset nếu mất liên kết đáng tin cậy hoặc đổi ứng viên.
- Chỉ dùng bằng chứng trong cửa sổ thời gian ngắn, loại kết quả từ camera generation/gallery version cũ.
- Cosine similarity được ghi tên đúng nếu xuất trong bảng nghiên cứu. UI chính dùng trạng thái nhận diện rõ ràng.
- Khung preview mirror và tọa độ khung mặt phải nhất quán. Pipeline CV xử lý ảnh theo quy ước đã kiểm tra.

## Đăng ký

- Nhập ID và họ tên khi đăng ký. Thông tin thật có thể bổ sung sau giai đoạn phát triển module.
- Chỉ chụp khi đúng một mặt đủ lớn, đủ sáng và đủ nét.
- Thu ba mẫu gồm chính diện, hơi quay trái và hơi quay phải, tránh ba bản sao của cùng frame.
- Cho phép chụp lại và hủy trước lưu.
- Kiểm tra ID trùng ở cả service và constraint database.
- Nếu embedding gần hồ sơ khác, cảnh báo khả năng đăng ký trùng để người thao tác xem lại. Ngưỡng cảnh báo cũng cần hiệu chỉnh.
- Lưu người và ba embedding trong một transaction. Reload gallery sau commit và reset lịch sử nhận diện.
- Hồ sơ nhận diện được đăng ký trên web và lưu trong DB backend thật, dùng được giữa các browser kết nối cùng backend. Đăng nhập email/mật khẩu và phân quyền chưa triển khai.

## Lưu và xuất

- Chỉ báo “Điểm danh thành công” sau commit SQLite.
- Ghi thất bại phải báo lỗi và có thể thử lại. Cache UI được cập nhật sau kết quả database.
- Database là nguồn tạo Excel. Cloud dùng PostgreSQL và download mode. Local dùng SQLite cùng daily exporter. File theo mẫu `attendance_YYYY_MM_DD.xlsx`.
- Các cột theo thứ tự `No.`, `ID`, `Full Name`, `Date`, `Time`, `Status`.
- ID và tên ghi như dữ liệu văn bản. Nội dung bắt đầu bằng ký tự có thể được Excel hiểu là công thức phải được ghi an toàn dưới dạng text và có bài kiểm tra khi triển khai.
- Xuất sắp theo recorded_at rồi attendance_id, đánh số từ 1, tên và thời gian lấy từ hàng điểm danh.
- Mỗi lần xuất dựng toàn bộ file từ snapshot ngày. Việc xuất lại không tạo hàng trùng.
- File tạm được hoàn tất trước khi thay file đích. Nếu thay thất bại, giữ bản đích trước đó và báo chờ cập nhật.
- Cập nhật revision trong cùng transaction ghi điểm danh để phục hồi xuất sau khi mở lại app.

## Dữ liệu cá nhân và bộ nộp

- Thu ảnh và dữ liệu thử khi người tham gia đồng ý, giải thích mục đích bài tập.
- Dữ liệu thật giữ local, loại dataset, embedding, database, export và log nhạy cảm khỏi Git khi tạo cấu hình repo.
- Dữ liệu để trong workspace có thể chịu cơ chế đồng bộ của thư mục OneDrive. Trước khi thu dữ liệu thật, thống nhất vị trí local và quyền chia sẻ trên máy demo.
- Log kỹ thuật ưu tiên mã lỗi, thời gian và request ID. Ảnh và embedding được quản lý trong dữ liệu chuyên biệt.
- Xóa dữ liệu thử sau bài tập theo thỏa thuận với người tham gia. Khi thêm thao tác xóa, xác định cả ảnh, mẫu, database, export và bản sao liên quan.

## Quy trình làm việc

- Mỗi đầu việc có chủ sở hữu và điều kiện hoàn thành trong TASKS.
- Thống nhất thay đổi hợp đồng qua INTERFACES trước khi sửa các module phụ thuộc.
- Nhánh làm việc theo tính năng, tích hợp bản chạy được mỗi ngày.
- Thay đổi model/runtime sau thử nghiệm cần cập nhật DECISIONS, metadata và kế hoạch tái tạo embedding.
- Khóa phiên bản dependencies và checksum model sau khi xác minh trên máy demo.
- Cuối ngày 3 đóng băng tính năng. Ngày 4 tập trung lỗi ảnh hưởng bài nộp.
- Ghi số liệu thực đo, số lượt và điều kiện thử. Nhận diện qua ảnh điện thoại là một kết quả kiểm thử cần công bố trung thực.

## Phê duyệt và UI

Chủ dự án đã duyệt và yêu cầu tích hợp FE–CV. UI web Next.js tiếng Anh đã nối FastAPI/SQLite theo phong cách authkit.com-DESIGN.md. Không seed/hardcode thành viên, ảnh hay bản ghi. Nhóm sẽ đăng ký từ website; dữ liệu kiểm thử phải ở DB riêng. localStorage chỉ lưu preferences, không dùng làm nơi lưu tài khoản/điểm danh. Xóa dữ liệu tự chụp thử đã được chủ dự án cho phép; không xóa hồ sơ thật sau đó để phục vụ demo. Shared backend key chỉ giữ ở server, không đưa vào bundle client. Cấu hình miễn phí dùng Vercel frontend, Render Free Python và Neon Free PostgreSQL; cấu hình theo DEPLOYMENT. Chế độ cloud dựng Excel lúc download để phù hợp filesystem tạm.
