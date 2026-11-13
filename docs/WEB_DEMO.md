# Demo thực từ website

## 1. Khởi chạy

Máy hiện tại đã có môi trường và hai model. Đóng cửa sổ CV standalone đang dùng webcam. Mở hai terminal từ thư mục gốc dự án.

Terminal backend:

```powershell
cd backend
.venv/Scripts/python.exe -m uvicorn presence_cv.api:app --host 127.0.0.1 --port 8000
```

Terminal frontend:

```powershell
cd frontend
npm run dev
```

Mở http://127.0.0.1:3000/attendance bằng Chrome hoặc Edge. Nếu server đang chạy, dùng luôn và không mở thêm server trên cùng cổng. Workspace phải báo dịch vụ kết nối; khi chưa có ai đăng ký, Members và Records trống.

Kiểm tra backend tại http://127.0.0.1:8000/api/health. Cài mới từ đầu xem [backend](../backend/README.md) và [frontend](../frontend/README.md).

## 2. Bạn đăng ký đầu tiên

1. Bấm **Create attendance profile** ở Attendance hoặc **Register member** trong Members.
2. Nhập **Full name** là họ tên đầy đủ có dấu và **Member ID** là MSSV/định danh duy nhất. ID được lưu dạng chuỗi, giữ số 0 ở đầu. Bấm **Continue**.
3. Bấm **Turn on camera**, chọn **Allow** khi trình duyệt hỏi. Giữ đúng một người trong khung, ánh sáng đều, đứng cách camera khoảng 40–70 cm.
4. Nhìn thẳng và bấm **Capture sample 1**. Chờ kiểm tra chấp nhận trước khi chụp tiếp.
5. Hơi quay đầu trái khoảng 10–15° và bấm **Capture sample 2**. Không cần quay 45° khi đăng ký.
6. Hơi quay phải và bấm **Capture sample 3**. Giữ mặt rõ, không che mắt/mũi.
7. Nếu ảnh bị từ chối, đọc thông báo rồi chỉnh ánh sáng/khoảng cách/tư thế và chụp lại. Nút **Retake samples** xóa bộ mẫu tạm để chụp lại ba ảnh.
8. Bấm **Review profile**, kiểm tra đúng tên, ID và đủ 3 ảnh. Bấm **Save profile**, chờ lưu hoàn tất.
9. Modal đóng và thẻ thành viên xuất hiện: hồ sơ đã được ghi vào database và gallery được nạp lại. Nếu chỉ đóng modal trước Save thì chưa tạo tài khoản.

Hệ thống tạo embedding bằng model pretrained đã có; thêm người không huấn luyện lại model. Luồng web lưu tên, ID,3 embedding cùng metadata; ảnh gốc không ghi ra đĩa. Không cần chuẩn bị thư mục ảnh hay sửa mã nguồn.

“Tài khoản” trong phiên bản này là hồ sơ nhận diện dùng cho điểm danh. Chưa có email/mật khẩu, trang đăng nhập hoặc quyền quản trị riêng.

## 3. Điểm danh

1. Sang **Attendance** → **Turn on camera**.
2. Nhìn camera, giữ mặt ổn định khoảng 0.5–1 giây ở điều kiện tốt. Thực tế phụ thuộc camera, CPU và mạng.
3. Khung mặt, landmark và tên được vẽ theo kết quả CV thật. Hệ thống cần ít nhất 3 quan sát nhất quán, tối thiểu 0.35 giây bằng chứng.
4. Chờ **Attendance successful** và hàng tên/ID/giờ xuất hiện trong Today’s arrivals. Thông báo này chỉ phát sau khi DB commit. Đứng yên một phút rồi kiểm tra vẫn chỉ có một hàng.
5. Chờ trạng thái Excel đồng bộ. Bấm **Export today to Excel** hoặc mở Records → **Export Excel**.
6. Bấm **Turn off camera**. Bật lại hoặc reload trang rồi thử cùng người: kết quả **Already checked in today**, số bản ghi vẫn 1 và giữ giờ đầu tiên.
7. Mở Members/Records từ trình duyệt khác hoặc sau restart backend: dữ liệu vẫn lấy từ cùng database.

Người chưa đăng ký hiển thị **Face not recognized** và không có bản ghi. Ảnh mờ/tối, mặt nhỏ hoặc tư thế chưa đạt sẽ yêu cầu điều chỉnh. Đứng yên trước camera không tạo nhiều hàng cùng ngày.

## 4. Kịch bản trình bày của nhóm

| Thời điểm | Việc làm |
| --- | --- |
| Trước buổi học | Bạn đăng ký đầu tiên, sau đó 1–2 thành viên tự đăng ký trên web |
| Trước demo | Kiểm tra mạng, webcam, ánh sáng, timezone; mở Members/Records thật |
| Trên lớp | Đăng ký 1–2 người còn lại từ đầu, giải thích3 góc mặt và Save |
| Demo nhận diện | Từng người lần lượt vào khung, chỉ ra tên và bản ghi mới |
| Demo chống trùng | Người đã có bản ghi vào lại, không tăng số hàng |
| Demo persistence | Reload trang, danh sách và bản ghi còn nguyên |
| Demo đầu ra | Tải Excel, đối chiếu ID dạng text và tên tiếng Việt |

Mỗi người chỉ điểm danh một lần/ngày. Ai đã thử điểm danh trước buổi thuyết trình trong cùng ngày sẽ nhận trạng thái đã điểm danh. Muốn có lần ghi mới trên lớp, dành ít nhất một người chưa điểm danh ngày đó; không xóa dữ liệu thật chỉ để tạo hiệu ứng demo.

Các bài tự động dùng database riêng và ảnh công khai. Chưa có ảnh thật của nhóm, vì vậy chưa có số liệu nhận diện nhóm. Sau khi đăng ký, Ân đo thời gian/nhận đúng/nhầm/từ chối theo [TEST_PLAN](TEST_PLAN.md).

## 5. Dữ liệu và lỗi thường gặp

| Tình huống | Xử lý |
| --- | --- |
| Service disconnected | Mở backend 8000, kiểm tra /api/health và frontend env, bấm Retry connection |
| Camera permission denied | Cho phép camera trong quyền trang rồi Retry camera |
| Không mở được camera | Đóng CV standalone/ứng dụng khác, chọn đúng browser, thử lại |
| Không thấy mặt | Đứng gần hơn, nhìn thẳng, ánh sáng từ trước |
| Low quality | Giữ yên, tránh ngược sáng, đừng quay quá nhiều |
| ID đã tồn tại | Kiểm tra Members; không đăng ký lại cùng ID |
| Similar face already registered | Có thể đã đăng ký dưới ID khác; xem lại hồ sơ |
| Ba ảnh không cùng danh tính / ảnh trùng | Retake samples và chụp lại cùng người với các góc nhẹ |
| Excel pending/error | Điểm danh đã lưu; đóng file Excel đang mở, bấm Retry export |
| Web Vercel không nhận diện | Kiểm tra backend HTTPS và persistent host; xem DEPLOYMENT |

Database mặc định: backend/var/attendance.sqlite3. Excel tự động: backend/var/exports/attendance_YYYY_MM_DD.xlsx. Xóa localStorage hoặc Reset preferences chỉ đổi giao diện, không xóa hồ sơ. Restart giữ cùng thư mục dữ liệu. Không commit DB/embedding/ảnh thật lên GitHub.

RGB recognition hiện chưa có liveness. Ảnh hoặc video có thể được nhận diện như người thật; không trình bày temporal confirmation là chống giả mạo.

## Demo bản cloud miễn phí

Làm theo DEPLOYMENT để tạo Neon trước, deploy Docker trên Render và nối Vercel. Mở web vài phút trước giờ demo, đợi dịch vụ sẵn sàng. UI tự thử lại khi backend đang thức dậy. Đăng ký/điểm danh đi cùng luồng bên trên; tốc độ cloud có thể cần giữ mặt ổn định lâu hơn laptop.

Cloud dùng PostgreSQL trên Neon. Trạng thái Excel là ready to download, tải workbook từ Records/Attendance. File được dựng lại từ database theo bộ lọc. Kiểm tra persistence bằng restart backend rồi mở lại danh sách. Nhóm tự đăng ký trên database cloud mới.
