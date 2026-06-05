# DESIGN DOCUMENT
## Bloom Filter Semi-Join Optimizer — "Subscribers & Logs"
### Đề tài #15 | Môn: Cơ Sở Dữ Liệu Phân Tán

---

## 1. Tổng Quan Kiến Trúc

### 1.1. Mô hình hệ thống phân tán

```
┌─────────────────────┐          Network          ┌─────────────────────┐
│      SITE A          │◄────────────────────────►│      SITE B          │
│   (HQ - Trụ sở)     │                          │  (Branch - Web)      │
│                      │   ① BF bit-vector →      │                      │
│   Subscribers        │   ② ← Filtered Logs      │   WebLogs            │
│   1,000,000 rows     │                          │   10,000,000 rows    │
│   (user_id, name,    │                          │   (log_id, user_id,  │
│    plan, fee)        │                          │    page, timestamp)  │
└─────────────────────┘                          └─────────────────────┘
```

### 1.2. Bài toán tối ưu

**Truy vấn:** `SELECT * FROM Subscribers S JOIN WebLogs W ON S.user_id = W.user_id`

- **Naive Join:** Gửi toàn bộ 10M rows (~1,430 MB) → ~80% là dữ liệu thừa
- **BF Semi-Join:** Gửi bit-vector ~1.14 MB → Site B lọc → chỉ gửi ~20% rows cần thiết

### 1.3. Quy trình Semi-Join 5 bước

| Bước | Vị trí | Hành động | Chi phí mạng |
|------|--------|-----------|--------------|
| 1 | Site A | Tạo BF từ user_ids (n=1M, FPR=1%) | 0 |
| 2 | A → B | Gửi BF bit-vector | ~1.14 MB |
| 3 | Site B | Lọc WebLogs qua BF, loại ~80% guest | 0 |
| 4 | B → A | Gửi filtered logs (~2M + FP rows) | ~306 MB |
| 5 | Site A | Inner Join cuối → loại FP, kết quả 100% | 0 |

**Tổng:** ~307 MB thay vì ~1,430 MB → **tiết kiệm ~78.5%**

---

## 2. Thiết Kế Chi Tiết

### 2.1. Bloom Filter (File 1)

**Cấu trúc dữ liệu:**
- Bit array kích thước `m` bits (tất cả khởi tạo = 0)
- `k` hàm băm độc lập (Double Hashing: MurmurHash3)

**Công thức tối ưu (theo Özsu & Valduriez):**
- Kích thước tối ưu: `m = -(n × ln(p)) / (ln2)²`
- Số hàm băm tối ưu: `k = (m/n) × ln(2)`
- FPR thực tế: `FPR = (1 - e^(-kn/m))^k`

**Đặc điểm then chốt:**
- False Negative = 0% (không bao giờ bỏ sót)
- False Positive > 0% (có thể nhận nhầm, nhưng kiểm soát được)

### 2.2. Data Generator (File 2)

| Bảng | Schema | Đặc điểm |
|------|--------|----------|
| Subscribers | user_id (PK), full_name, email, plan, monthly_fee | Dữ liệu Việt Nam, 4 gói cước |
| WebLogs | log_id (PK), user_id (FK), page, method, status, timestamp | Overlap ratio cấu hình được |

### 2.3. Semi-Join Simulator (File 3)

So sánh 2 chiến lược với 3 bảng metric:
1. **Bảng 1:** So sánh băng thông mạng (KB)
2. **Bảng 2:** Bytes saved vs BF size (m bits) — **metric chính đề bài**
3. **Bảng 3:** FPR impact on wasted bandwidth

### 2.4. Technology Stack

| Thành phần | Công nghệ | Lý do chọn |
|------------|-----------|------------|
| Hash function | MurmurHash3 (mmh3) | Nhanh, phân bố đều, non-cryptographic |
| Bit storage | bitarray | Tiết kiệm bộ nhớ, O(1) access |
| Data processing | Pandas | Mô phỏng database operations |
| Visualization | Matplotlib + Chart.js | Terminal + Web dashboard |
| Web framework | Flask | Nhẹ, đơn giản, phù hợp demo |
| Hashing technique | Double Hashing | Kirsch & Mitzenmacher (2006) |
