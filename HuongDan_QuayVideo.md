# 📹 KỊCH BẢN QUAY VIDEO DEMO & THUYẾT TRÌNH ĐẠT ĐIỂM TỐI ĐA (3 - 5 PHÚT)
## Đề tài #15: Bloom Filter Join Optimizer — Tối ưu hóa truy vấn phân tán

---

## 🛠️ PHẦN CHUẨN BỊ (Trước khi bấm quay)
* **Phần mềm quay:** Sử dụng **OBS Studio** hoặc **Xbox Game Bar** (`Win + G`). Thiết lập chất lượng quay tối thiểu **1080p** để thầy cô nhìn rõ từng con số trên Dashboard.
* **Giao diện làm việc:** 
  * Cửa sổ trình duyệt mở sẵn Dashboard (`http://localhost:5000`), phóng to (zoom) lên **110% - 120%**.
  * 2 cửa sổ Terminal đặt cạnh nhau ở nửa dưới màn hình để thể hiện tính phân tán (Site A chạy port 5000, Site B chạy port 5001).

---

## 🎬 KỊCH BẢN NÓI VÀ THAO TÁC CHI TIẾT

### ⏱️ PHẦN 1: Giới thiệu đề tài & Khởi động (0:00 – 0:40)
* **Hành động trên màn hình:**
  * Bật quay màn hình khi đang ở giao diện 2 Terminal trống.
  * Lần lượt gõ lệnh khởi động 2 Server:
    * Terminal 1 (Site B): `python site_b_server.py`
    * Terminal 2 (Site A): `python app.py`
  * Chuyển sang trình duyệt và nhấn F5 tải lại trang Dashboard.
* **Lời thoại nói (Nói chậm rãi, tự tin):**
  * *"Kính chào Thầy/Cô, em tên là [Tên Bạn], đại diện nhóm thực hiện đề tài **Tối ưu hóa truy vấn phân tán sử dụng Bloom Filter Semi-Join**."*
  * *"Trước hết, em khởi động hệ thống phân tán gồm hai site độc lập: **Site B** đóng vai trò là Web Server lưu trữ dữ liệu nhật ký web lớn tại cổng 5001, và **Site A** đóng vai trò là Trạm điều phối trung tâm lưu trữ thông tin khách hàng tại cổng 5000."*
  * *"Hệ thống đã sẵn sàng giao tiếp thông qua REST API, và đây là trang Dashboard điều khiển trung tâm của nhóm."*

---

### ⏱️ PHẦN 2: Demo Chạy Bình Thường — So sánh Hiệu năng (0:40 – 2:00)
* **Hành động trên màn hình:**
  * Di chuột qua các ô cấu hình dữ liệu (ví dụ: Số lượng dòng của 2 bảng, tỷ lệ overlap, False Positive Rate - FPR).
  * Kiểm tra nút trạng thái Node B đang hiển thị **ONLINE (màu xanh)**.
  * Click vào nút **"Chạy Mô Phỏng" (Run Simulation)**.
  * Khi kết quả xuất hiện, dùng chuột rê vào từng con số thống kê và biểu đồ so sánh.
* **Lời thoại nói:**
  * *"Ở kịch bản đầu tiên, hệ thống hoạt động trong điều kiện lý tưởng, hai Node đều Online. Em thiết lập các tham số đầu vào và nhấn chạy mô phỏng."*
  * *"Quá trình thực thi diễn ra như sau: Site A tạo một mảng băm Bloom Filter thu gọn từ danh sách khóa của mình, gửi qua mạng đến Site B. Site B dùng cấu trúc này lọc nhanh dữ liệu WebLogs rồi gửi ngược lại các dòng thỏa mãn về cho Site A thực hiện Inner Join cuối cùng."*
  * *"Hãy nhìn vào bảng so sánh hiệu năng truyền tải mạng:"*
    * **[Chỉ chuột vào Naive Join Bandwidth]** *"Với phương pháp Naive Join truyền thống, ta phải truyền toàn bộ dữ liệu thô của Site B qua mạng, tiêu tốn khoảng **[đọc con số trên màn hình, ví dụ: 7.3 MB]**."*
    * **[Chỉ chuột vào BF Semi-Join Bandwidth]** *"Nhưng với Bloom Filter Semi-Join ở mức sai số giả 1%, lượng băng thông tiêu thụ giảm xuống chỉ còn **[đọc con số, ví dụ: 1.5 MB]** — tức là chúng ta đã **tiết kiệm thành công gần 79%** băng thông mạng."*
    * **[Chỉ chuột vào Leverage]** *"Chỉ số Leverage đạt **[ví dụ: 1000x]**, nghĩa là cứ 1 byte dữ liệu Bloom Filter gửi đi giúp tiết kiệm được 1000 bytes truyền tải thô."*
    * **[Chỉ chuột vào Số dòng kết quả]** *"Đặc biệt, kết quả JOIN hoàn toàn chính xác 100%, chứng minh rằng mặc dù Bloom Filter tồn tại tỷ lệ False Positive (sai sót giả), nhưng thuật toán đã loại bỏ hoàn toàn các dòng dư thừa này ở bước đối khớp cuối cùng tại Site A."*

---

### ⏱️ PHẦN 3: Kịch bản Chịu lỗi — Kill Node B (2:00 – 3:15)
* **Hành động trên màn hình:**
  * Chuyển sang Tab cấu hình hệ thống hoặc Click vào nút giả lập **"Sập Node B" (Simulate Node B Failure / Offline)**.
  * Switch chuyển sang màu đỏ báo hiệu Node B **OFFLINE**. Chờ 2 giây.
  * Nhấn nút **"Chạy Mô Phỏng"** lần nữa.
  * Chỉ chuột vào sơ đồ Pipeline: Bước 1 (Tạo Bloom Filter tại Site A) hiện xanh lá (Success), nhưng Bước 2 (Gửi sang Site B) đổi sang màu đỏ kèm thông báo lỗi kết nối (Timeout/Connection Refused). Banner cảnh báo hệ thống sập xuất hiện.
* **Lời thoại nói:**
  * *"Tiếp theo, em xin demo kịch bản quan trọng nhất của hệ thống phân tán: **Khả năng chịu lỗi và đảm bảo tính nhất quán của giao dịch** khi có sự cố mạng."*
  * *"Em tiến hành ngắt kết nối Node B. Trạng thái Node B lúc này đã chuyển sang OFFLINE."*
  * *"Em thực hiện lại truy vấn. Hệ thống tại Site A vẫn tiến hành tạo Bloom Filter thành công (Bước 1). Tuy nhiên, khi gửi yêu cầu sang Site B, hệ thống phát hiện mất kết nối mạng và lập tức trả về lỗi HTTP 504 Timeout (Bước 2)."*
  * *"Thay vì bị treo tiến trình vô hạn hoặc ghi nhận dữ liệu lỗi, hệ thống của nhóm đã tự động kích hoạt cơ chế **Abort Transaction (Hủy giao dịch)** và thực hiện Rollback trạng thái một cách an toàn, đảm bảo tính nhất quán dữ liệu theo đúng lý thuyết thiết kế của hệ cơ sở dữ liệu phân tán."*

---

### ⏱️ PHẦN 4: Khôi phục hệ thống (3:15 – 4:00)
* **Hành động trên màn hình:**
  * Click vào nút **"Khôi phục Node B" (Recover Node B)** hoặc bật lại Switch sang **ONLINE**.
  * Nhấn nút **"Chạy Mô Phỏng"** lần thứ 3.
  * Kết quả tính toán hiện ra bình thường, chính xác 100%.
* **Lời thoại nói:**
  * *"Bây giờ, em thực hiện khôi phục lại kết nối cho Node B. Hệ thống tự động ping kiểm tra và chuyển trạng thái Node B sang ONLINE."*
  * *"Em nhấn chạy lại mô phỏng lần thứ ba. Giao dịch phân tán được thực hiện lại từ đầu và cho ra kết quả chính xác 100% ngay lập tức mà quản trị viên không cần phải khởi động lại toàn bộ máy chủ."*

---

### ⏱️ PHẦN 5: Kết luận & Điểm sáng (4:00 – 4:30)
* **Hành động trên màn hình:**
  * Di chuột toàn cảnh màn hình Dashboard, dừng lại ở bảng so sánh tổng quan.
* **Lời thoại nói (Nói dứt khoát, chuyên nghiệp):**
  * *"Tóm lại, thông qua ứng dụng demo, nhóm chúng em đã chứng minh thực nghiệm thành công ba vấn đề cốt lõi:"*
  * *"**Một:** Thuật toán Bloom Filter Semi-Join tối ưu hóa cực tốt băng thông mạng trong môi trường phân tán (tiết kiệm gần 79% dữ liệu truyền tải)."*
  * *"**Hai:** Đảm bảo độ chính xác tuyệt đối của kết quả truy vấn cuối cùng nhờ cơ chế lọc hai lớp."*
  * *"**Ba:** Hệ thống có khả năng tự phát hiện lỗi kết nối, tự động cô lập và khôi phục giao dịch để bảo toàn tính nhất quán của dữ liệu."*
  * *"Em xin chân thành cảm ơn Thầy/Cô đã theo dõi phần demo của nhóm. Chúng em rất mong nhận được những câu hỏi và ý kiến đóng góp từ Thầy/Cô."*

---

## 💡 CÁC KEYWORDS "ĂN ĐIỂM VÀNG" KHI THẦY CÔ VẤN ĐÁP
Nếu thầy cô ngắt lời hoặc hỏi sâu hơn trong lúc bảo vệ, hãy sử dụng chính xác các cụm từ chuyên ngành sau:

1. **Khi hỏi về lý thuyết tối ưu hóa:** 
   * *"Nhóm áp dụng nguyên lý **Semi-Join** để giảm kích thước bảng trung gian trước khi truyền qua mạng. Thay vì truyền cả bảng lớn, nhóm chỉ truyền cấu trúc tóm tắt bộ lọc **Bloom Filter** dạng mảng bit (Bit Array) có kích thước cực kỳ nhỏ."*
2. **Khi hỏi về độ chính xác (False Positive):**
   * *"Bloom Filter chỉ có sai sót giả (**False Positive** - phần tử không thuộc tập hợp nhưng bộ lọc báo có) và hoàn toàn không có sai sót sót (**False Negative** - báo không có nhưng thực chất là có). Do đó, dữ liệu lọc từ Site B gửi về Site A có thể dư một vài dòng (do False Positive), nhưng khi thực hiện phép toán **Inner Join** cuối cùng tại Site A, các dòng dư thừa này sẽ bị loại bỏ hoàn toàn. Vì vậy, kết quả JOIN cuối cùng đạt độ chính xác 100%."*
3. **Khi hỏi về thiết kế hệ thống phân tán:**
   * *"Hệ thống được thiết kế theo mô hình **Khách - Chủ (Client-Server)** và giao tiếp phi trạng thái (**Stateless REST API**), giúp dễ dàng mở rộng và phục hồi trạng thái khi xảy ra sự cố sập node mạng (Fault Tolerance)."*
