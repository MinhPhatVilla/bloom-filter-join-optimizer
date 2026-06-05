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

### Yêu cầu
- Python 3.8+
- pip

### Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Chạy Demo (Terminal)
```bash
python 5_main_demo.py
```
Pipeline sẽ tự động:
1. Tạo dữ liệu giả lập (100K Subscribers + 1M WebLogs)
2. Chạy Naive Join vs BF Semi-Join (4 mức FPR)
3. In bảng so sánh chi tiết
4. Tính toán lý thuyết cho quy mô 1M/10M
5. Vẽ dashboard 4 biểu đồ → lưu `dashboard.png`

### Chạy Web Dashboard
```bash
python app.py
```
Mở trình duyệt: **http://localhost:5000**

---

## 📂 Cấu trúc dự án

```
Do_an_cuoi_ki_csdl_pt/
├── 1_bloom_filter.py      # Cài đặt Bloom Filter từ scratch
├── 2_data_generator.py     # Tạo dữ liệu giả lập 2 site
├── 3_semi_join.py          # So sánh Naive Join vs BF Semi-Join
├── 4_visualization.py      # Vẽ dashboard 4 biểu đồ
├── 5_main_demo.py          # Pipeline tổng hợp (chạy file này!)
├── app.py                  # Flask web dashboard
├── templates/index.html    # Giao diện web
├── static/css/style.css    # Styling
├── static/js/app.js        # Logic frontend
├── requirements.txt        # Dependencies
├── BaoCao_PhanTich.md      # Báo cáo phân tích (Özsu & Valduriez)
├── Design_Document.md      # Tài liệu thiết kế 2 trang
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
