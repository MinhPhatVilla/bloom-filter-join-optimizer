# ĐỀ CƯƠNG DỰ ÁN CƠ SỞ DỮ LIỆU PHÂN TÁN
## DISTRIBUTED DATABASE PROJECT PROPOSAL

- **Due Date:** [Điền ngày nộp - Tuần 3]
- **Project ID & Category:** #15: Bloom Filter Join Optimizer - Category 3 (Tối ưu hóa Truy vấn Phân tán)

---

### 1. Project Identity (Thông tin nhóm)
- **Team Name:** [Điền tên nhóm của bạn - Ví dụ: BloomBand / FilterFlow / DataShield]
- **Team Members:** 
  1. [Họ và tên thành viên 1 - MSSV]
  2. [Họ và tên thành viên 2 - MSSV]
- **Project Title:** Thiết kế và Đánh giá Bộ Tối ưu hóa Phép Nối Phân Tán sử dụng Bloom Filter Semi-Join cho Hệ thống Subscribers & WebLogs
*(Bloom Filter Semi-Join Query Optimizer for Distributed Subscriber & WebLog Systems)*

---

### 2. Objective & Problem Statement (Mục tiêu & Bài toán)
- **The "Why" (Lý do thực hiện):** 
  Trong hệ cơ sở dữ liệu phân tán, việc thực hiện phép nối (`JOIN`) hai bảng lớn nằm ở hai Site khác nhau qua đường truyền mạng là một "nút thắt cổ chai" (bottleneck) lớn về mặt băng thông và thời gian phản hồi. 
  Nếu truyền toàn bộ dữ liệu thô chưa qua lọc từ Site B sang Site A (phương pháp Naive Join), lượng băng thông tiêu thụ sẽ rất lớn, trong đó có tới 80% là dữ liệu thừa của những người dùng không tồn tại ở Site A (guest/anonymous logs).
  Dự án này giải quyết bài toán tối ưu hóa băng thông bằng cách áp dụng thuật toán **Bloom Filter Semi-Join** để lọc dữ liệu thừa ngay tại Site nguồn trước khi truyền tải qua mạng. Chúng tôi sẽ phân tích mối quan hệ đánh đổi (trade-off) giữa kích thước của vector bit ($m$ bits), số lượng hàm băm ($k$), tỷ lệ lỗi dương tính giả (False Positive Rate - FPR) và băng thông mạng tiết kiệm được.

- **Core Logic (Thuật toán cốt lõi):**
  Thuật toán **Bloom Filter Semi-Join** gồm 5 bước chính:
  1. **Tạo Bloom Filter tại Site A:** Trích xuất toàn bộ khóa nối `user_id` từ bảng `Subscribers` (1 triệu dòng), băm qua $k$ hàm băm và ánh xạ vào vector bit kích thước $m$ bits.
  2. **Truyền Bloom Filter:** Gửi vector bit siêu nhỏ này từ Site A sang Site B qua mạng.
  3. **Lọc dữ liệu tại Site B:** Duyệt qua bảng dữ liệu `WebLogs` (10 triệu dòng) tại Site B. Kiểm tra `user_id` của từng dòng log với Bloom Filter nhận được. Chỉ giữ lại những dòng log có `user_id` cho kết quả khớp (chấp nhận một lượng nhỏ False Positives).
  4. **Truyền kết quả lọc:** Site B gửi các dòng log đã lọc (chỉ khoảng 20% dung lượng gốc) ngược lại Site A.
  5. **Khớp nối cuối cùng tại Site A:** Thực hiện phép `Inner Join` thực tế giữa bảng `Subscribers` và các dòng log nhận được để loại bỏ hoàn toàn các lỗi dương tính giả (False Positives), đảm bảo kết quả truy vấn chính xác 100%.

---

### 3. Dataset Specification (Đặc tả dữ liệu)
- **Source (Nguồn dữ liệu):** Dữ liệu giả lập có cấu trúc thực tế (Sinh tự động bằng Python script chuyên biệt `2_data_generator.py` để chủ động kiểm soát tỷ lệ trùng khớp khóa nối giữa hai Site).
- **Size (Kích thước):**
  - **Site A (Subscribers):** 1,000,000 dòng dữ liệu người dùng (~80 MB thô).
  - **Site B (WebLogs):** 10,000,000 dòng nhật ký hoạt động Web (~1.2 GB thô).
- **Schema (Lược đồ dữ liệu):**
  - **Subscribers (Bảng thông tin khách hàng tại Site A):**
    - `user_id` (Primary Key - UUID/String): Mã định danh duy nhất của người dùng.
    - `full_name` (String): Tên đầy đủ của khách hàng (tiếng Việt).
    - `email` (String): Địa chỉ email.
    - `plan` (String): Gói dịch vụ đăng ký (Free, Bronze, Silver, Gold).
    - `monthly_fee` (Float): Phí thuê bao hàng tháng.
  - **WebLogs (Bảng nhật ký hoạt động tại Site B):**
    - `log_id` (Primary Key - UUID/String): Mã định danh duy nhất của dòng log.
    - `user_id` (Foreign Key - String): Mã định danh người dùng thực hiện hành động.
    - `page` (String): Trang web được truy cập (ví dụ: `/home`, `/dashboard`, `/checkout`).
    - `method` (String): Phương thức HTTP (GET, POST).
    - `status` (Integer): Mã trạng thái HTTP (200, 404, 500).
    - `timestamp` (DateTime): Thời gian ghi nhận log.
- **Fragmentation Strategy (Chiến lược phân tán):**
  Phân tán ngang (Horizontal Fragmentation) theo vị trí địa lý vật lý:
  - Bảng `Subscribers` được lưu trữ tập trung tại Site A (Trụ sở chính quản lý khách hàng).
  - Bảng `WebLogs` được lưu trữ tại Site B (Web Server đặt tại Data Center ghi nhận lượng truy cập khổng lồ).

---

### 4. System Architecture (Kiến trúc hệ thống)
- **Nodes (Số lượng nút):** Giả lập 2 sites chính:
  - **Site A (Client/Trụ sở):** Nơi khởi tạo truy vấn và nhận kết quả cuối cùng.
  - **Site B (Server/Chi nhánh):** Nơi lưu giữ lượng nhật ký WebLogs khổng lồ.
- **Communication Layer (Lớp giao tiếp):**
  - Giao tiếp giữa các tiến trình/module thông qua Web API (HTTP/REST sử dụng Flask).
  - Có bộ giám sát lưu lượng mạng (Network Traffic Monitor) để tính toán chính xác dung lượng truyền tải thực tế (tính bằng Bytes/Kilobytes) của từng gói tin (Bloom Filter bit-vector và Filtered WebLogs).
- **Storage (Lưu trữ):**
  - Dữ liệu được lưu trữ dạng tập tin Parquet/CSV cục bộ tại mỗi Site để mô phỏng tính độc lập dữ liệu.
  - Tải dữ liệu vào bộ nhớ dưới dạng Pandas DataFrame để thực hiện mô phỏng truy vấn và tính toán các chỉ số tối ưu.

---

### 5. Tech Stack & Implementation Plan (Công nghệ & Kế hoạch triển khai)
- **Programming Language (Ngôn ngữ lập trình):** Python 3.8+ (tối ưu hóa xử lý mảng và cấu trúc dữ liệu lớn).
- **Deployment (Triển khai):**
  - Chạy local dưới dạng ứng dụng dịch vụ Web Flask.
  - Giao diện người dùng Web Dashboard trực quan viết bằng HTML5/CSS3/Vanilla JS giúp cấu hình tham số động trực tiếp trên trình duyệt.
- **Libraries/Frameworks (Thư viện sử dụng):**
  - `mmh3` (MurmurHash3): Hàm băm phi mã hóa tốc độ cao, phân bố đều bit, dùng để triển khai Bloom Filter.
  - `bitarray`: Thư viện xử lý mảng bit tối ưu bộ nhớ RAM cấp thấp trong Python.
  - `pandas`: Xử lý, nối và truy vấn dữ liệu lớn ở mỗi Node.
  - `Flask`: Tạo RESTful API mô phỏng giao tiếp mạng và phục vụ Web Dashboard trực quan.
  - `Chart.js` / `matplotlib`: Vẽ biểu đồ động thể hiện sự biến thiên của băng thông theo tỷ lệ FPR và kích thước mảng bit ngay trên Web Dashboard.

---

### 6. Success Metrics & Analysis (Chỉ số đo lường hiệu năng)
- **Quantitative Metric (Chỉ số định lượng):**
  - **Băng thông tiết kiệm được (Bytes saved):** Tính bằng công thức $Bytes\_Saved = Bandwidth_{Naive} - Bandwidth_{BF\_Semi\_Join}$.
  - **Tỷ lệ tiết kiệm băng thông (Bandwidth Savings %):** Mục tiêu đạt trên 70% lượng băng thông giảm tải.
  - **Savings Leverage (Độ bẩy băng thông):** Tỷ lệ giữa lượng byte mạng tiết kiệm được chia cho kích thước vật lý của Bloom Filter ($m$ bits).
  - **False Positive Rate (FPR) thực nghiệm:** So sánh với FPR lý thuyết để chứng minh tính đúng đắn của giải thuật băm kép (Double Hashing).
- **The "Failure" Scenario (Kịch bản lỗi/thử thách hệ thống):**
  Chúng tôi sẽ mô phỏng kịch bản cấu hình sai lệch tham số Bloom Filter:
  - **Mô phỏng bộ lọc quá nhỏ ($m$ nhỏ):** Khi giảm kích thước $m$ của Bloom Filter để tiết kiệm băng thông gửi đi ở Bước 2, tỷ lệ lỗi FPR sẽ tăng lên đột ngột (ví dụ: FPR > 30%). Điều này dẫn đến việc Site B lọc không hiệu quả, gửi nhầm hàng triệu dòng log rác (False Positives) về Site A.
  - **Đánh giá điểm gãy (Break-even Point):** Xác định ngưỡng giới hạn tối thiểu của kích thước Bloom Filter mà tại đó tổng chi phí mạng của thuật toán Semi-Join (bao gồm kích thước Bloom Filter + lượng dữ liệu rác truyền về) bắt đầu vượt quá chi phí truyền thô Naive Join, từ đó tìm ra công thức tối ưu hóa chi phí mạng cho hệ thống.

---

### 7. Project Milestones (Mốc thời gian dự án)
- **Milestone 1 (Week 5):** Thiết lập môi trường lập trình. Hoàn thành script sinh dữ liệu ngẫu nhiên phân tán (1M Subscribers tại Site A và 10M WebLogs tại Site B) và lưu trữ cục bộ dưới dạng CSV/Parquet.
- **Milestone 2 (Week 8):** Hiện thực hóa cấu trúc dữ liệu Bloom Filter tối ưu (băm kép Double Hashing sử dụng MurmurHash3 và bitarray). Hoàn thành pipeline thực thi Semi-Join hoàn chỉnh và kiểm chứng độ chính xác 100% của kết quả phép nối cuối cùng.
- **Milestone 3 (Week 12):** Phát triển giao diện Web Dashboard mô phỏng trực quan. Thực hiện các bài test benchmark với các kích thước Bloom Filter khác nhau ($m$), vẽ biểu đồ phân tích hiệu năng và hoàn thiện báo cáo phân tích chi tiết nộp giảng viên.
