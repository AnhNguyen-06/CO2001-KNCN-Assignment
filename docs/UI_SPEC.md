# Yêu cầu giao diện và tiếp nhận thiết kế

## Trạng thái thiết kế

Chủ dự án đã cung cấp [authkit.com-DESIGN.md](authkit.com-DESIGN.md) và duyệt dựng frontend trước CV. Giao diện dùng tiếng Anh, triển khai trong `frontend/` bằng Next.js App Router, React và TypeScript. Tên làm việc Presence được chọn để dựng nhận diện sản phẩm riêng.

Phong cách dùng nền #05060f, heading gradient #d8ecf8 → #98c0ef, viền kính blue-white alpha thấp, capsule phát sáng, construction lines, circuit và instrument nguyên bản. Dùng Inter cho nội dung và Manrope cho heading theo font thay thế trong design guide, đóng gói local qua Fontsource.

Hiệu ứng gồm perimeter/circuit 12 giây, radar 40 giây, spotlight 6 và 8,5 giây, entrance/reveal nhẹ và hover inset lighting. Hỗ trợ reduced motion từ hệ điều hành và Settings.

## Routes và ranh giới phiên bản frontend

| Route | Chức năng |
| --- | --- |
| / | Landing với product fan tương tác, workflow circuit và đường dẫn workspace |
| /attendance | Camera realtime, CV thật, chống trùng qua SQLite, danh sách trong ngày |
| /members | Tìm kiếm, chi tiết thành viên, đăng ký ba mẫu |
| /records | Search, filter ngày/ID, phân trang, tải Excel theo view |
| /settings | Mirror, guide, reduced motion, reset có xác nhận |

Browser quản lý webcam, gửi JPEG qua Next.js proxy đến FastAPI. Đã tích hợp quality gate, embeddings, matching, lưu SQLite và Excel tự động. Hồ sơ/bản ghi lấy từ backend; localStorage chỉ giữ preferences. Landing dùng minh họa workflow chung, không có danh tính cứng. Hợp đồng tại INTERFACES, hướng dẫn thực tại WEB_DEMO.

## Các vùng chức năng

| Vùng | Nội dung cần có |
| --- | --- |
| Đầu trang | Tên ứng dụng, ngày giờ và trạng thái sẵn sàng |
| Camera chính | Live preview, bounding box và nhãn từng mặt |
| Điều khiển | Bật/tắt camera, đăng ký, retry và tải Excel |
| Số liệu ngày | Số ID đã điểm danh trong ngày hiện tại |
| Hoạt động vừa ghi | Họ tên, ID, thời gian của bản ghi trong ngày từ DB |
| Trạng thái Excel | Đã đồng bộ, đang xuất, chờ cập nhật, lỗi có thể thử lại |

Phương án sơ bộ là camera bên trái và thao tác/danh sách bên phải. Tỷ lệ và vị trí cuối cùng theo mẫu được chọn.

## Hộp thoại đăng ký

- Hai trường ID/MSSV và họ tên, lỗi hiển thị tại trường tương ứng.
- Preview dùng camera service chung.
- Ba ô mẫu, có hướng dẫn chính diện và hơi quay trái/phải.
- Chụp, chụp lại, lưu, hủy.
- Cho lưu khi đủ ba mẫu hợp lệ và thông tin hợp lệ.
- Phản hồi khi không có mặt, nhiều mặt, ảnh mờ/tối, ID trùng và lỗi lưu.
- Hiển thị bước lưu và cập nhật gallery. Thành viên mới dùng được ngay khi gallery tải thành công.

## Trạng thái hiển thị bắt buộc

| Tình huống | Nội dung/hành động |
| --- | --- |
| Camera tắt | Hướng dẫn bật camera |
| Gallery trống | Hướng dẫn đăng ký thành viên |
| Đang mở camera | Chỉ báo đang mở, khóa thao tác lặp |
| Không có mặt | Hướng dẫn đứng vào vùng camera |
| Ảnh chưa đạt | Hướng dẫn cụ thể theo chất lượng |
| Không xác định | Nhãn rõ ràng, giữ trạng thái chờ |
| Đang xác nhận | Phản hồi ngắn, tránh nhấp nháy gây hiểu nhầm |
| Điểm danh thành công | Tên, thời gian và hàng mới sau commit |
| Đã điểm danh | Thời gian gốc hôm nay |
| Camera lỗi | Thử lại và gợi ý kiểm tra thiết bị |
| Excel lỗi | Báo dữ liệu đã lưu, cho thử cập nhật |

Thông báo điểm danh dùng dạng không chặn preview. Màu đi kèm chữ hoặc icon để nhận biết trạng thái. Nút có nhãn rõ ràng, trạng thái disabled phù hợp với tác vụ đang chạy.

## Font và độ phân giải

- Nội dung UI dùng tiếng Anh. Họ tên cá nhân vẫn hỗ trợ Unicode và dấu tiếng Việt.
- Ghi tên font, weights, cỡ chữ và cách cung cấp font trên máy thứ hai.
- Nếu font thiếu hoặc không dùng được trong framework, trình bày lựa chọn thay thế để chủ dự án quyết định.
- Kiểm tra trên màn hình laptop và Windows scaling thực tế, tránh cắt bảng/nút.
- Họ tên dài, ID có số 0 đầu và thông báo lỗi dài đều phải đọc được.
- Preview giữ đúng tỷ lệ khung hình. Bounding box và tên đi cùng vị trí mặt khi mirror/resize.

## Thông tin tiếp nhận qua mẫu/MCP

| Hạng mục | Cần xác định |
| --- | --- |
| Nguồn mẫu | Trang/file/frame cụ thể và quyền truy cập |
| Màn hình | Màn hình điểm danh, đăng ký, trạng thái lỗi/rỗng nếu có |
| Typography | Font family, weights, size và nguồn font |
| Design tokens | Màu, spacing, border, radius, shadow |
| Assets | Logo/icon và file có thể sử dụng |
| Tương tác | Hover, disabled, thông báo, mở/đóng hộp thoại |

## Nghiệm thu UI

So sánh bản dựng với mẫu tại cùng kích thước cửa sổ, xác minh font và tiếng Việt, đi hết luồng bằng nút, thử mọi trạng thái lỗi chính và kiểm tra giao diện còn phản hồi trong lúc nhận diện/xuất file. Kết quả đối chiếu sẽ được ghi sau triển khai.
