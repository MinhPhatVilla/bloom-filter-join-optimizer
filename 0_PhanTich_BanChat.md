# 📚 PHÂN TÍCH BẢN CHẤT DỰ ÁN: BLOOM FILTER JOIN OPTIMIZER

> File này được tạo ra để **giải thích cốt lõi (bản chất)** của từng file code trong dự án. Đọc hiểu file này sẽ giúp em nắm vững 100% logic để tự tin bảo vệ trước thầy cô. Mình sẽ liên tục cập nhật file này khi tạo thêm các file code mới.

---

## 🟢 FILE 1: `1_bloom_filter.py` — "Cái Rổ Lọc Ma Thuật"

### 1. Bản chất file này dùng để làm gì?
File này xây dựng cấu trúc dữ liệu **Bloom Filter** từ con số 0 (from scratch). Em hãy tưởng tượng Bloom Filter giống như một **"chiếc rổ lọc"** vô cùng nhỏ gọn nhưng cực kỳ thông minh. 

Nó giúp trả lời câu hỏi: *"User ID này có nằm trong danh sách khách hàng của tôi không?"* một cách SIÊU NHANH và tốn SIÊU ÍT BỘ NHỚ.

### 2. Sự "Ma Thuật" nằm ở đâu?
Thông thường, nếu em có 1 triệu User ID, em phải lưu lại toàn bộ 1 triệu ID đó để kiểm tra (tốn khoảng 10MB - 15MB).
Nhưng với Bloom Filter, em **không hề lưu lại các User ID đó**. Em chỉ băm (hash) các User ID thành những điểm đánh dấu trên một dải ruy-băng (bit array). Dải ruy-băng này chỉ tốn khoảng **1.14 MB** (tiết kiệm gần 90%).

### 3. Đánh đổi (Trade-off) cốt lõi:
Cái gì cũng có giá của nó. Vì nó quá nhỏ gọn nên nó **đôi khi bị nhầm lẫn nhỏ**:
- Nó có thể **nhầm một người lạ thành khách hàng** (False Positive > 0). Ví dụ: Em hỏi "GUEST_123 có phải khách hàng không?", nó đáp "CÓ THỂ CÓ" (nhưng thực tế là không). Tỷ lệ nhầm này em kiểm soát được (ví dụ setup cho nó nhầm 1% thôi).
- Nhưng nó **KHÔNG BAO GIỜ bỏ sót khách hàng thật** (False Negative = 0). Nếu là khách hàng thật, nó chắc chắn sẽ nhận ra.

### 4. Tại sao đồ án Phân Tán lại cần file này?
Vì trong môi trường Phân Tán, gửi dữ liệu qua mạng rất chậm và tốn kém (Network Bandwidth). Thay vì gửi nguyên một danh sách 1 triệu ID từ Server A sang Server B (tốn 10MB bandwidth), Server A chỉ cần gửi cái "rổ lọc Bloom Filter" này (tốn 1MB bandwidth). 

---

## 🟢 FILE 2: `2_data_generator.py` — "Nhà Máy Sản Xuất Hiện Thực"

### 1. Bản chất file này dùng để làm gì?
Hệ thống phân tán cần phải có dữ liệu ở nhiều nơi khác nhau để demo. File này đóng vai trò là "nhà máy" tự động sinh ra dữ liệu giả lập cho 2 Server (Site A và Site B) sao cho giống với thực tế nhất.

### 2. Cấu trúc dữ liệu được sinh ra:
*   **SITE A (Trụ sở chính): Bảng `Subscribers` (Khách hàng trả phí)**
    *   Lưu thông tin: User ID, Tên, Email, Gói cước (Basic/Premium...), Phí hàng tháng.
    *   Số lượng: Ít (ví dụ: 10.000 user).

*   **SITE B (Chi nhánh Web Server): Bảng `WebLogs` (Nhật ký truy cập web)**
    *   Lưu thông tin: Log ID, User ID (ai đang truy cập), Trang web nào (/home, /login...), Thời gian.
    *   Số lượng: Rất nhiều (ví dụ: 50.000 bản ghi).

### 3. Bản chất của "Sự Lãng Phí" (Overlap) mà file này mô phỏng:
Khi một người vào trang web của em (được ghi lại trong `WebLogs` ở Site B), người đó có thể là:
1.  **Khách hàng thật (Subscriber):** Chiếm khoảng 20% - 35% lượt truy cập.
2.  **Khách vãng lai (Guest):** Chiếm tới 65% - 80% lượt truy cập.

**Bài toán đặt ra cho hệ thống CSDL Phân Tán:** 
Site A muốn tính toán xem khách hàng của mình truy cập trang web nào nhiều nhất. 
*   **Cách ngu ngốc (Naive):** Site B bốc toàn bộ 50.000 dòng WebLogs gửi qua mạng cho Site A. Trong 50.000 dòng này, có tới 80% là của "khách vãng lai", Site A nhận về cũng vứt đi vì không join được với bảng Subscribers. → **Lãng phí 80% băng thông mạng!**
*   **Cách thông minh:** Dùng file 1 (Bloom Filter) lọc vứt đi 80% khách vãng lai ngay tại Site B, chỉ gửi 20% khách hàng thật qua Site A thôi.

---

## 🟢 FILE 3: `3_semi_join.py` — "Chiến Trường So Tài Của Thuật Toán"

### 1. Bản chất file này dùng để làm gì?
Đây là file **TRỌNG TÂM** của toàn bộ đồ án. Nó tổ chức một "cuộc đua" giữa 2 phương pháp Join dữ liệu phân tán:
- **Phương pháp 1: NAIVE JOIN** (Làm theo kiểu truyền thống ngây thơ - Gửi hết dữ liệu qua mạng rồi mới Join).
- **Phương pháp 2: BLOOM FILTER SEMI-JOIN** (Làm theo kiểu thông minh - Gửi "Rổ lọc" đi trước, Lọc xong mới gửi dữ liệu thật về).

File này sẽ ghi lại toàn bộ "thời gian" và "băng thông mạng (network bytes)" tiêu tốn của 2 phương pháp để đưa ra kết luận.

### 2. Các bước cốt lõi của Bloom Filter Semi-Join (Phương pháp 2) diễn ra thế nào?
Hãy tưởng tượng luồng đi dữ liệu như sau:
*   **Bước 1 (Tại Site A):** Lấy danh sách 10.000 khách hàng nhét vào Bloom Filter để biến thành một "chiếc rổ lọc" nhỏ xíu (chỉ tốn khoảng 17 KB).
*   **Bước 2 (Gửi đi):** Site A gửi rổ lọc 17 KB này bay qua mạng internet đến Site B.
*   **Bước 3 (Tại Site B):** Site B nhận rổ lọc, đem 50.000 dòng log đi qua rổ lọc này. Những dòng log của "khách vãng lai" sẽ bị vứt đi ngay lập tức (loại bỏ được ~80% rác). Chỉ còn lại những dòng lọt qua rổ lọc.
*   **Bước 4 (Gửi về):** Site B đóng gói những dòng log "sạch" lọt qua rổ (tầm ~10.000 dòng) và gửi trả lại qua mạng về Site A.
*   **Bước 5 (Tại Site A):** Site A đem số log sạch này Join với bảng khách hàng của mình để ra kết quả cuối cùng. Bất kỳ hạt sạn nào lọt qua rổ lọc (False Positive) cũng sẽ bị loại bỏ ở bước Join cuối cùng này.

### 3. Điều quan trọng nhất để em nói với thầy cô về File 3 này:
*"Dạ thưa thầy/cô, điều tuyệt vời nhất của Bloom Filter Semi-Join là sự an toàn tuyệt đối. Mặc dù Bloom Filter có lỗi nhận nhầm (False Positive - nó nhầm khách vãng lai thành khách hàng), làm cho Site B vô tình gửi dư một ít rác về lại Site A. Tuy nhiên, điều này chỉ làm tốn thêm một chút xíu băng thông, chứ **KHÔNG BAO GIỜ LÀM SAI LỆCH KẾT QUẢ CUỐI CÙNG**. Bởi vì ở bước cuối cùng tại Site A, khi thực hiện phép Inner Join thực sự, mọi dòng log rác đó sẽ tự động bị loại bỏ do không khớp với bất kỳ User ID thực tế nào."*


## 🟢 FILE 4: `4_visualization.py` — "Người Kể Chuyện Bằng Hình Ảnh"

### 1. Bản chất file này dùng để làm gì?
File này nhận kết quả số liệu khô khan từ File 3 và biến chúng thành **4 biểu đồ trực quan đẹp** hiển thị trên cùng một dashboard. Thay vì đọc hàng chục con số, giảng viên nhìn vào biểu đồ là hiểu ngay kết luận.

### 2. Bốn biểu đồ được vẽ là gì?

| Biểu đồ | Loại | Thể hiện điều gì? |
|---|---|---|
| **Biểu đồ 1** | Cột (Bar) | So sánh băng thông mạng: Naive tốn bao nhiêu KB, mỗi BF tiết kiệm được bao nhiêu % |
| **Biểu đồ 2** | Đường (Line) | FPR cài đặt (lý thuyết) có khớp với FP đo được thực tế không? |
| **Biểu đồ 3** | Diện tích (Stackplot) | Khi Overlap thấp → phần lãng phí chiếm tỷ lệ rất lớn → BF cần thiết |
| **Biểu đồ 4** | Đường (Line) | Bloom Filter càng nhỏ FPR (chính xác hơn) thì phải tốn nhiều bit hơn |

### 3. Điểm ghi điểm với giảng viên:
- File này **không phụ thuộc vào kết quả cụ thể** — em chỉ cần truyền vào list kết quả bất kỳ là nó tự vẽ đẹp.
- Kết quả được **lưu thành file `dashboard.png`** → dễ chèn vào báo cáo Word/PowerPoint.

---

## 🟢 FILE 5: `5_main_demo.py` — "Nhạc Trưởng Điều Phối Toàn Bộ"

### 1. Bản chất file này dùng để làm gì?
Đây là file **DUY NHẤT** em cần chạy khi demo trước thầy cô. Nó đóng vai trò như một "nhạc trưởng" — gọi đúng thứ tự 4 file còn lại và kết hợp chúng thành một pipeline hoàn chỉnh từ đầu đến cuối.

### 2. Pipeline (Luồng chạy) của File 5:
```
python 5_main_demo.py
       |
       |-- [Buoc 1] Goi File 2 tao du lieu gia lap (Subscribers + WebLogs)
       |-- [Buoc 2] Goi File 3 chay Naive Join va BF Semi-Join, do ket qua
       |-- [Buoc 3] In Bang Bao Cao tong ket ra man hinh (so sanh chi tiet)
       |-- [Buoc 4] Goi File 4 ve Dashboard va luu file dashboard.png
       |
       => Xong! Toan bo chi mat ~15 giay.
```

### 3. Kết quả sau khi chạy File 5:
- **Trên màn hình terminal:** Bảng so sánh đầy đủ giữa các chiến lược.
- **File `dashboard.png` mới được tạo:** Dashboard 4 biểu đồ đẹp, sẵn sàng chụp ảnh chèn báo cáo.
- **Kết luận rõ ràng:** BF Semi-Join FPR 0.1% tiết kiệm được ~80% chi phí băng thông mạng với độ chính xác 100%.

---

## 📋 TỔNG KẾT TOÀN DỰ ÁN (SAU KHI KIỂM TRA VÀ HOÀN THIỆN)

| File | Vai trò | Khi nào chạy? |
|---|---|---|
| `1_bloom_filter.py` | Cài đặt "rổ lọc" Bloom Filter | Được File 3, 5 gọi tự động |
| `2_data_generator.py` | Tạo dữ liệu giả lập 2 site | Được File 5 gọi tự động |
| `3_semi_join.py` | So tài Naive vs BF — **3 bảng metric chuẩn đề bài** | Được File 5 gọi tự động |
| `4_visualization.py` | Vẽ biểu đồ dashboard | Được File 5 gọi tự động |
| **`5_main_demo.py`** | **Điều phối tất cả + Lý thuyết 1M/10M** | **Chỉ cần chạy file này!** |

### Các metric đề bài yêu cầu đã được đáp ứng đầy đủ:

| Yêu cầu đề bài | Đã làm |
|---|---|
| Dataset: Subscribers 1M, WebLogs 10M | ✅ Demo 100K/1M (tỷ lệ 1:10), tính lý thuyết 1M/10M |
| BF minimizes data transfer A→B→A | ✅ 5 bước Semi-Join được mô phỏng đầy đủ |
| Calculate False Positive Rate | ✅ FPR lý thuyết + đo thực tế, so sánh 4 mức |
| FPR impact on wasted bandwidth | ✅ Bảng 3 trong File 3 |
| **Metric: Bytes saved vs size of bit-vector (m bits)** | ✅ **Bảng 2 trong File 3, mục [4]-[6] trong báo cáo** |

> **Lệnh demo duy nhất cần nhớ:** `python 5_main_demo.py`
