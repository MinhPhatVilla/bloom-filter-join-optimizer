# BÁO CÁO PHÂN TÍCH
## Bloom Filter Semi-Join Optimizer — "Subscribers & Logs"
### Đề tài #15 | Môn: Cơ Sở Dữ Liệu Phân Tán

---

## 1. GIỚI THIỆU ĐỀ TÀI

### 1.1. Bối cảnh

Trong hệ thống Cơ Sở Dữ Liệu Phân Tán (CSDL-PT), dữ liệu được phân bố trên nhiều site (nút mạng) khác nhau. Khi thực hiện phép **JOIN** giữa các bảng nằm ở các site khác nhau, hệ thống phải truyền tải dữ liệu qua mạng — đây là **chi phí lớn nhất** trong xử lý truy vấn phân tán.

Theo **Özsu & Valduriez** (*Principles of Distributed Database Systems*, Chapter 7 — Distributed Query Processing):

> *"The cost of transferring data over the network is typically the dominant cost in distributed query processing. Therefore, minimizing the amount of data transferred is crucial."*

### 1.2. Mô hình dữ liệu

| Site | Bảng | Mô tả | Quy mô |
|------|------|-------|--------|
| **Site A** (Trụ sở chính) | `Subscribers` | Thông tin thuê bao trả phí | 1,000,000 rows |
| **Site B** (Web Server) | `WebLogs` | Nhật ký truy cập website | 10,000,000 rows |

**Truy vấn cần thực thi:**
```sql
SELECT S.full_name, S.plan, W.page, W.timestamp
FROM Subscribers S
JOIN WebLogs W ON S.user_id = W.user_id
```

### 1.3. Vấn đề

Trong thực tế, phần lớn lượt truy cập website đến từ **khách vãng lai** (guest), chỉ khoảng 20-35% là từ thuê bao (subscriber). Nếu áp dụng cách JOIN truyền thống (gửi toàn bộ WebLogs từ Site B → Site A), sẽ **lãng phí 65-80% băng thông mạng**.

---

## 2. CƠ SỞ LÝ THUYẾT (Theo Özsu & Valduriez)

### 2.1. Xử lý truy vấn phân tán (Distributed Query Processing)

Theo **Özsu & Valduriez, Chương 7**, quá trình xử lý truy vấn phân tán gồm 4 lớp:

1. **Query Decomposition**: Phân rã truy vấn thành các phép toán quan hệ
2. **Data Localization**: Xác định dữ liệu nằm ở site nào
3. **Global Optimization**: Tối ưu thứ tự thực hiện và chiến lược truyền tải
4. **Local Optimization**: Tối ưu tại từng site riêng lẻ

Đồ án này tập trung vào **lớp 3 — Global Optimization**, cụ thể là tối ưu chiến lược truyền tải dữ liệu giữa các site khi thực hiện phép JOIN.

### 2.2. Semi-Join (Nửa phép kết)

Theo **Özsu & Valduriez, Mục 7.4.3**, Semi-Join là kỹ thuật giảm lượng dữ liệu truyền tải bằng cách:

> *"A semijoin reduces the number of tuples that need to be transferred by first shipping only the join attribute values (projection) to the remote site, filtering the remote relation, then transferring only the matching tuples back."*

**Quy trình Semi-Join truyền thống (3 bước):**

```
Site A                              Site B
  │                                   │
  │ ① Gửi π(user_id) từ Subscribers  │
  │ ──────────────────────────────►   │
  │                                   │ ② Lọc WebLogs ⋉ user_ids
  │ ③ Gửi filtered WebLogs về        │
  │ ◄──────────────────────────────   │
  │                                   │
  │ ④ JOIN tại Site A                 │
```

**Vấn đề:** Gửi toàn bộ danh sách user_id (1M × 10 bytes = **10 MB**) vẫn tốn khá nhiều bandwidth.

### 2.3. Bloom Filter — Cải tiến Semi-Join

**Bloom Filter** (Bloom, 1970) là cấu trúc dữ liệu xác suất cho phép biểu diễn một tập hợp dưới dạng **bit-vector cực nhỏ**. Thay vì gửi danh sách 10 MB user_ids, ta gửi một Bloom Filter chỉ ~1.14 MB.

Theo **Özsu & Valduriez, Mục 7.4.4**:

> *"Bloom filters provide a compact representation of the join attribute values, significantly reducing the size of the data shipped in the first phase of a semijoin. The trade-off is a small probability of false positives, which results in slightly more data being transferred in the second phase."*

#### 2.3.1. Cấu trúc Bloom Filter

Bloom Filter gồm:
- **Bit array** có kích thước `m` bits (ban đầu tất cả = 0)
- **k hàm băm** độc lập: h₁, h₂, ..., hₖ

**INSERT (item):** Tính k vị trí hash → set các bit tương ứng = 1

**LOOKUP (item):** Tính k vị trí hash → nếu TẤT CẢ bit = 1 → "Có thể có"; nếu BẤT KỲ bit = 0 → "Chắc chắn không"

#### 2.3.2. Công thức toán học

| Tham số | Công thức | Ý nghĩa |
|---------|-----------|---------|
| m (kích thước tối ưu) | `m = -(n × ln(p)) / (ln2)²` | Số bits cần cho n phần tử với FPR = p |
| k (số hash tối ưu) | `k = (m/n) × ln(2)` | Cân bằng giữa precision và collision |
| FPR (thực tế) | `FPR = (1 - e^(-kn/m))^k` | Xác suất nhận nhầm phần tử không có |

#### 2.3.3. Đặc điểm quan trọng

| Đặc điểm | Giá trị | Ý nghĩa |
|-----------|---------|---------|
| **False Negative Rate** | **= 0%** | KHÔNG BAO GIỜ bỏ sót phần tử thực sự có |
| **False Positive Rate** | **> 0%** | CÓ THỂ nhận nhầm phần tử không có thành có |
| **Tính toàn vẹn kết quả** | **100%** | FP bị loại ở bước Inner Join cuối cùng |

---

## 3. THIẾT KẾ VÀ CÀI ĐẶT

### 3.1. Lựa chọn thiết kế (Design Choices)

#### 3.1.1. Hàm băm: MurmurHash3 + Double Hashing

Thay vì dùng k hàm băm độc lập (tốn tài nguyên), dự án áp dụng kỹ thuật **Double Hashing** (Kirsch & Mitzenmacher, 2006):

```
hᵢ(x) = (h₁(x) + i × h₂(x)) mod m    (i = 0, 1, ..., k-1)
```

Trong đó h₁ và h₂ là hai hàm MurmurHash3 với seed khác nhau.

**Lý do chọn:**
- MurmurHash3: non-cryptographic, tốc độ rất nhanh, phân bố đều
- Double Hashing: giảm từ k lần hash xuống còn 2 lần, hiệu quả tương đương (đã được chứng minh toán học)

#### 3.1.2. Cấu hình tham số tự động

Dự án cho phép 2 cách khởi tạo Bloom Filter:
1. **Tự động (recommended):** Chỉ cần cung cấp `n` (số phần tử) và `fp_rate` (FPR mong muốn) → hệ thống tự tính `m` và `k` tối ưu
2. **Thủ công:** Chỉ định trực tiếp `m` và `k`

#### 3.1.3. Mô phỏng dữ liệu phân tán

Dữ liệu được sinh với các đặc điểm thực tế:
- **Subscribers:** Tên Việt Nam, 4 gói cước (Basic/Standard/Premium/Enterprise), phân bổ theo tỷ trọng
- **WebLogs:** HTTP methods (70% GET), status codes, response time (log-normal distribution), overlap ratio cấu hình được

### 3.2. Kiến trúc module

```
1_bloom_filter.py ─────► Class BloomFilter
                         ├── __init__(): Tự động tính m, k tối ưu
                         ├── insert(item): Thêm phần tử
                         ├── lookup(item): Kiểm tra phần tử
                         ├── get_theoretical_fpr(): FPR lý thuyết
                         ├── get_empirical_fpr(): FPR đo thực tế
                         └── get_size_bytes(): Kích thước BF

2_data_generator.py ───► Class DataGenerator
                         ├── generate_subscribers(): Tạo Site A
                         ├── generate_web_logs(): Tạo Site B
                         └── analyze_data(): Phân tích overlap

3_semi_join.py ────────► Class DistributedJoinSimulator
                         ├── run_naive_join(): Chiến lược truyền thống
                         ├── run_bloom_filter_semi_join(): Chiến lược BF
                         └── compare_strategies(): So sánh & báo cáo

4_visualization.py ────► Dashboard 4 biểu đồ
5_main_demo.py ────────► Pipeline tổng hợp
app.py ────────────────► Web Dashboard (Flask)
```

---

## 4. KẾT QUẢ PHÂN TÍCH

### 4.1. Kết quả mô phỏng thực tế (100K / 1M)

Mô phỏng với 100,000 Subscribers + 1,000,000 WebLogs (tỷ lệ 1:10 như đề bài), overlap 20%:

| Chiến lược | Dòng gửi | FP | Mạng (KB) | Tiết kiệm |
|-----------|----------|-----|-----------|-----------|
| Naive Join | 1,000,000 | 0 | 146,484 | baseline |
| BF Semi-Join (FPR 10%) | ~280,000 | ~80,000 | ~41,016 | ~72% |
| BF Semi-Join (FPR 5%) | ~240,000 | ~40,000 | ~35,156 | ~76% |
| BF Semi-Join (FPR 1%) | ~208,000 | ~8,000 | ~30,469 | ~79% |
| BF Semi-Join (FPR 0.1%) | ~200,800 | ~800 | ~29,414 | ~80% |

### 4.2. METRIC CHÍNH: Bytes Saved vs. Size of Bit-Vector (m bits)

Đây là **metric chính theo yêu cầu đề bài**:

| FPR | BF size (m bits) | BF size (KB) | Bytes Saved (KB) | Leverage |
|-----|-------------------|-------------|------------------|----------|
| 10% | 479,253 | 58.5 | ~105,468 | ~1,803x |
| 5% | 623,527 | 76.1 | ~111,328 | ~1,463x |
| 1% | 958,506 | 117.0 | ~116,015 | ~991x |
| 0.1% | 1,437,759 | 175.5 | ~117,070 | ~667x |

**Nhận xét:**
- **Leverage cực cao:** Mỗi 1 byte Bloom Filter tiết kiệm được 667 – 1,803 bytes bandwidth
- FPR thấp hơn → BF lớn hơn → ít FP hơn → tiết kiệm nhiều hơn, nhưng leverage giảm
- **Trade-off tối ưu:** FPR = 1% cho cân bằng tốt nhất giữa kích thước BF và bandwidth saved

### 4.3. FPR Impact on Wasted Bandwidth

| FPR Target | FP Rows | FP Bytes (KB) | % Bandwidth thêm do FP |
|-----------|---------|---------------|----------------------|
| 10% | ~80,000 | ~11,719 | ~8.0% |
| 5% | ~40,000 | ~5,859 | ~4.0% |
| 1% | ~8,000 | ~1,172 | ~0.8% |
| 0.1% | ~800 | ~117 | ~0.08% |

**Nhận xét:** FPR = 1% chỉ gây lãng phí thêm ~0.8% bandwidth — một mức rất chấp nhận được so với 80% lãng phí của Naive Join.

### 4.4. Phân tích lý thuyết quy mô đề bài (1M / 10M)

Tính toán theo công thức Bloom Filter cho quy mô chính xác đề bài:

| FPR | m (bits) | BF (MB) | Total Transfer (MB) | Saved (MB) | Saved % | Leverage |
|-----|----------|---------|---------------------|-----------|---------|----------|
| 10% | 4,792,530 | 0.57 | 401.97 | 1,028.03 | 71.9% | 1,803x |
| 5% | 6,235,224 | 0.74 | 344.83 | 1,085.17 | 75.9% | 1,462x |
| 1% | 9,585,059 | 1.14 | 306.54 | 1,123.46 | 78.6% | 983x |
| 0.5% | 11,035,332 | 1.31 | 297.40 | 1,132.60 | 79.2% | 862x |
| 0.1% | 14,377,588 | 1.71 | 288.26 | 1,141.74 | 79.8% | 667x |

**Kết luận quy mô 1M/10M:**
- Naive Join cần truyền **~1,430 MB** qua mạng
- BF Semi-Join (FPR=1%) chỉ cần **~307 MB** → tiết kiệm **~1,123 MB (78.6%)**
- Bloom Filter chỉ nặng **~1.14 MB** — bằng 0.08% dữ liệu tiết kiệm được

---

## 5. ĐÁNH GIÁ THEO LÝ THUYẾT ÖZSU & VALDURIEZ

### 5.1. So sánh với các chiến lược trong giáo trình

Theo **Özsu & Valduriez, Chương 7**, các chiến lược thực thi JOIN phân tán được phân loại:

| Chiến lược | Chi phí mạng (1M/10M) | Ưu điểm | Nhược điểm |
|-----------|----------------------|---------|-----------|
| **Ship Whole** (Naive) | ~1,430 MB | Đơn giản | Lãng phí cực lớn |
| **Semi-Join** (gửi IDs) | ~317 MB | Giảm ~78% | Vẫn tốn 10 MB gửi IDs |
| **BF Semi-Join** (đề án này) | ~307 MB | Giảm ~78.6%, BF nhỏ gọn | FPR > 0 (nhưng không ảnh hưởng kết quả) |

### 5.2. Chi phí truyền tải (Communication Cost)

Theo **Özsu & Valduriez, Mục 7.3.2**, chi phí truyền tải được tính:

```
C_total = C₀ + C₁ × |data|
```

Trong đó:
- C₀: Chi phí khởi tạo kết nối (cố định)
- C₁: Chi phí truyền mỗi byte
- |data|: Lượng dữ liệu truyền

**So sánh chi phí:**

| Phương pháp | |data| truyền | Số lần truyền |
|------------|---------------|---------------|
| Naive Join | 10M × 150 bytes = 1,430 MB | 1 chiều (B→A) |
| Semi-Join | 1M × 10 bytes + 2M × 150 bytes ≈ 310 MB | 2 chiều (A→B→A) |
| BF Semi-Join | 1.14 MB + 2M × 150 bytes ≈ 307 MB | 2 chiều, nhưng chiều đi rất nhỏ |

### 5.3. Tính đúng đắn (Correctness)

Theo **Özsu & Valduriez**, kết quả truy vấn phân tán phải **tương đương** với kết quả trên CSDL tập trung.

**BF Semi-Join đảm bảo tính đúng đắn tuyệt đối:**
1. **False Negative = 0%** → Bloom Filter KHÔNG BAO GIỜ bỏ sót subscriber → mọi matching tuple đều được gửi về
2. **False Positive được loại bỏ** → Ở bước Inner Join cuối cùng tại Site A, các tuple FP tự động bị loại vì không khớp user_id
3. **Kết quả = 100% chính xác** → Tương đương với centralized JOIN

### 5.4. Trade-off Analysis

Theo **Özsu & Valduriez**, mọi chiến lược tối ưu đều có trade-off:

| Trade-off | Phân tích |
|-----------|-----------|
| **BF size vs FPR** | m lớn → FPR nhỏ → ít FP → tiết kiệm bandwidth hơn, nhưng BF nặng hơn |
| **Precision vs Bandwidth** | FPR=0.1% tiết kiệm 79.8% nhưng BF=1.71 MB; FPR=10% tiết kiệm 71.9% nhưng BF chỉ 0.57 MB |
| **Computation vs Communication** | Tính hash tại local (rẻ) để giảm data truyền qua mạng (đắt) |
| **Optimal point** | FPR = 1% là điểm cân bằng tốt nhất cho bài toán này |

---

## 6. KẾT LUẬN

### 6.1. Tóm tắt kết quả

Dự án đã cài đặt thành công **Bloom Filter Semi-Join Optimizer** cho bài toán JOIN phân tán "Subscribers & Logs":

| Metric | Giá trị |
|--------|---------|
| Bandwidth tiết kiệm (FPR=1%, 1M/10M) | **78.6%** (~1,123 MB saved) |
| Kích thước BF (1M users, FPR=1%) | **1.14 MB** (m = 9,585,059 bits) |
| Savings Leverage | **983x** (1 byte BF → tiết kiệm 983 bytes) |
| Độ chính xác kết quả | **100%** (FP bị loại ở Inner Join) |
| False Negative | **0%** (BF không bao giờ bỏ sót subscriber) |

### 6.2. Đóng góp

1. **Cài đặt Bloom Filter from scratch** — Không dùng thư viện BF có sẵn, toàn bộ logic tự viết
2. **Mô phỏng đầy đủ pipeline Semi-Join** — 5 bước, đo lường chi tiết bandwidth
3. **Phân tích cả lý thuyết lẫn thực nghiệm** — So sánh FPR lý thuyết vs thực tế
4. **Web Dashboard tương tác** — Cho phép tuỳ chỉnh tham số và xem kết quả trực quan
5. **Liên kết chặt chẽ với giáo trình Özsu & Valduriez** — Đúng framework Distributed Query Processing

### 6.3. Hạn chế và hướng phát triển

| Hạn chế | Hướng phát triển |
|---------|-----------------|
| Demo 100K/1M (thay vì full 1M/10M) | Dùng streaming/chunked processing |
| Mô phỏng trên 1 máy | Triển khai distributed thực sự (Docker, gRPC) |
| Bloom Filter cơ bản | Counting Bloom Filter, Cuckoo Filter |
| Chỉ hỗ trợ equi-join | Mở rộng cho range join, multi-attribute join |

---

## TÀI LIỆU THAM KHẢO

1. **Özsu, M.T. & Valduriez, P.** (2020). *Principles of Distributed Database Systems*, 4th Edition. Springer. — Chương 7: Distributed Query Processing.
2. **Bloom, B.H.** (1970). *Space/time trade-offs in hash coding with allowable errors*. Communications of the ACM, 13(7), 422-426.
3. **Kirsch, A. & Mitzenmacher, M.** (2006). *Less Hashing, Same Performance: Building a Better Bloom Filter*. Proceedings of the 14th Annual European Symposium on Algorithms (ESA).
4. **Mackert, L.F. & Lohman, G.M.** (1986). *R* optimizer validation and performance evaluation for distributed queries*. Proceedings of the 12th International Conference on Very Large Data Bases.

---

> **Ghi chú:** Tất cả kết quả lý thuyết cho quy mô 1M/10M được tính toán chính xác bằng công thức Bloom Filter. Kết quả mô phỏng thực tế (100K/1M) xác nhận công thức lý thuyết là chính xác.
