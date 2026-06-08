# 🔬 Bloom Filter Semi-Join Optimizer
## Đề tài #15: "Subscribers & Logs"

> **Môn học:** Cơ Sở Dữ Liệu Phân Tán  
> **Tham khảo lý thuyết:** Özsu & Valduriez — *Principles of Distributed Database Systems*

---

## 📌 Mô tả đề tài

Sử dụng **Bloom Filter** để tối ưu hoá truyền tải dữ liệu trong phép JOIN phân tán giữa 2 site:

| Site | Bảng | Quy mô |
|------|------|--------|
| **Site A** (Trụ sở) | `Subscribers` — Thuê bao trả phí | 1,000,000 rows |
| **Site B** (Chi nhánh) | `WebLogs` — Nhật ký truy cập | 10,000,000 rows |

**Truy vấn cần thực thi:**
```sql
SELECT S.full_name, S.plan, W.page, W.timestamp
FROM Subscribers S JOIN WebLogs W ON S.user_id = W.user_id
```

**Vấn đề:** Nếu gửi toàn bộ 10M WebLogs qua mạng → ~80% là dữ liệu thừa (khách vãng lai).  
**Giải pháp:** Site A gửi compact bit-vector (Bloom Filter) → Site B lọc trước → chỉ gửi ~20% dữ liệu cần thiết.

---

## 🚀 Cài đặt & Chạy

### Yêu cầu hệ thống
- Python 3.8+
- Các thư viện trong `requirements.txt` (`Flask`, `pandas`, `bitarray`, `mmh3`, `requests`, `matplotlib`, v.v.)

### Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Cách 1: Chạy Demo trực tiếp trên Terminal (Mô phỏng Offline)
```bash
python 5_main_demo.py
```
*Lưu ý trên Windows:* Nếu gặp lỗi font hiển thị tiếng Việt, bạn có thể chạy lệnh:
```powershell
$env:PYTHONIOENCODING="utf-8"; python 5_main_demo.py
```
Pipeline sẽ tự động:
1. Tạo dữ liệu giả lập (100K Subscribers + 1M WebLogs).
2. Chạy Naive Join vs BF Semi-Join (4 mức FPR).
3. In bảng so sánh chi tiết và tính toán lý thuyết cho quy mô lớn 1M/10M.
4. Vẽ dashboard 4 biểu đồ trực quan và lưu thành file `dashboard.png`.

### Cách 2: Chạy Web Dashboard & Thực nghiệm Phân tán thực tế (2 Nodes)
Để chứng minh hệ thống hoạt động phân tán thực sự giữa 2 Site độc lập giao tiếp qua mạng:

1. **Khởi chạy Site B (Web Server - port 5001):**
   Mở một Terminal mới và chạy:
   ```bash
   python site_b_server.py
   ```
2. **Khởi chạy Site A (Trung tâm & Dashboard - port 5000):**
   Mở thêm một Terminal khác và chạy:
   ```bash
   python app.py
   ```
3. **Truy cập Giao diện Web:**
   Mở trình duyệt và truy cập: **http://localhost:5000**
   - **Chạy mô phỏng online:** Đặt tham số trên panel và bấm nút **"Chạy Mô Phỏng"**. Bạn sẽ thấy pipeline mô phỏng 5 bước truyền tin hoạt động cực kỳ mượt mà.
   - **Kiểm thử khả năng chịu lỗi (Fault Tolerance):** Trên giao diện, tắt switch **"Trạng thái Node B"** sang **OFFLINE** (hoặc tắt tiến trình `site_b_server.py` ở Terminal 1) rồi bấm chạy lại. Giao diện sẽ báo lỗi kết nối và hủy giao dịch phân tán (Abort Transaction), khôi phục trạng thái an toàn. Bạn có thể bấm nút **"Khôi phục Node B"** để kết nối lại bình thường.

---

## 📂 Cấu trúc dự án

```
Do_an_cuoi_ki_csdl_pt/
├── 0_PhanTich_BanChat.md   # Phân tích bản chất bài toán
├── 1_bloom_filter.py       # Cài đặt Bloom Filter từ scratch
├── 2_data_generator.py     # Tạo dữ liệu giả lập 2 site
├── 3_semi_join.py          # So sánh Naive Join vs BF Semi-Join
├── 4_visualization.py      # Vẽ dashboard 4 biểu đồ
├── 5_main_demo.py          # Pipeline tổng hợp (chạy file này!)
├── app.py                  # Flask web dashboard (Site A)
├── site_b_server.py        # Flask server cho Site B (port 5001)
├── generate_docx.py        # Script tạo báo cáo .docx
├── generate_pptx.py        # Script tạo slide .pptx
├── templates/index.html    # Giao diện web
├── static/css/style.css    # Styling
├── static/js/app.js        # Logic frontend
├── requirements.txt        # Dependencies
└── dashboard.png           # Biểu đồ kết quả
```

---

## 📊 Kết quả chính

| Metric | Giá trị |
|--------|---------|
| Bandwidth tiết kiệm (FPR=0.1%) | ~80% |
| Kích thước BF (1M users, FPR=1%) | ~1.14 MB |
| Savings Leverage | ~1,100x (1 byte BF → tiết kiệm 1,100 bytes) |
| Độ chính xác kết quả | 100% (FP bị loại ở Inner Join cuối) |
| False Negative | 0% (BF không bao giờ bỏ sót subscriber) |

---

## 📚 Tham khảo

- Özsu, M.T. & Valduriez, P. (2020). *Principles of Distributed Database Systems*, 4th Edition. Springer.
- Bloom, B. (1970). *Space/time trade-offs in hash coding with allowable errors*. Communications of the ACM.
- Kirsch, A. & Mitzenmacher, M. (2006). *Less Hashing, Same Performance: Building a Better Bloom Filter*.
