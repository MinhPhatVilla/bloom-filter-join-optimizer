"""
==========================================================================
FILE 2: DATA GENERATOR - Tạo Dữ Liệu Giả Lập Phân Tán
==========================================================================
Môn: Cơ Sở Dữ Liệu Phân Tán
Đề tài: Bloom Filter Join Optimizer - "Subscribers & Logs"

File này tạo dữ liệu cho BÀI TOÁN PHÂN TÁN:

   ┌─────────────────┐                ┌─────────────────────┐
   │    SITE A        │                │      SITE B          │
   │  (HQ - Trụ sở)  │    Network     │  (Branch - Chi nhánh)│
   │                  │◄──────────────►│                      │
   │  Subscribers     │                │     WebLogs          │
   │  (Thuê bao)      │                │  (Nhật ký truy cập)  │
   └─────────────────┘                └─────────────────────┘

Bài toán: JOIN Subscribers với WebLogs theo user_id
  → Cần tối ưu lượng dữ liệu truyền qua mạng
  → Dùng Bloom Filter Semi-Join

Đặc điểm dữ liệu:
  - Subscribers: ÍT hơn (vd: 10,000 người dùng trả phí)
  - WebLogs: NHIỀU hơn (vd: 50,000 - 100,000 bản ghi)
  - Overlap: Chỉ ~30-50% WebLogs match với Subscribers
    → Nếu gửi hết WebLogs qua mạng → LÃNG PHÍ bandwidth
    → Bloom Filter giúp lọc trước ở Site B
==========================================================================
"""

import random
import string
import pandas as pd
from datetime import datetime, timedelta


class DataGenerator:
    """
    Bộ tạo dữ liệu giả lập cho hệ thống phân tán.
    
    Tạo 2 bảng:
    1. subscribers (Site A): Thông tin người dùng đã đăng ký
    2. web_logs (Site B): Nhật ký truy cập website
    
    Dữ liệu được thiết kế sao cho:
    - Có MỘT PHẦN web_logs match với subscribers (overlap)
    - Có NHIỀU web_logs không match (guest/anonymous users)
    → Mô phỏng thực tế: không phải ai vào web cũng là thuê bao
    """
    
    def __init__(self, seed=42):
        """
        Khởi tạo DataGenerator với random seed cố định.
        
        Parameters:
            seed (int): Random seed để đảm bảo kết quả reproducible.
                        Mỗi lần chạy với cùng seed → cùng dữ liệu.
        """
        self.seed = seed
        random.seed(seed)
        
        # ===== Cấu hình sinh dữ liệu =====
        # Danh sách tên giả lập (dùng cho Subscribers)
        self.first_names = [
            "An", "Bình", "Cường", "Dũng", "Hải", "Hòa", "Hùng",
            "Khoa", "Lan", "Linh", "Long", "Mai", "Minh", "Nam",
            "Ngọc", "Phong", "Quân", "Sơn", "Thảo", "Tùng",
            "Tuấn", "Uyên", "Vân", "Việt", "Xuân", "Yến",
            "Đạt", "Phúc", "Trung", "Hương"
        ]
        self.last_names = [
            "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh",
            "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ",
            "Hồ", "Ngô", "Dương", "Lý"
        ]
        
        # Danh sách gói dịch vụ (subscription plans)
        self.plans = [
            ("Basic", 99000),       # 99,000 VNĐ/tháng
            ("Standard", 199000),   # 199,000 VNĐ/tháng
            ("Premium", 399000),    # 399,000 VNĐ/tháng
            ("Enterprise", 999000)  # 999,000 VNĐ/tháng
        ]
        self.plan_weights = [0.40, 0.30, 0.20, 0.10]  # Tỷ lệ phân bổ
        
        # Các trang web được truy cập (cho WebLogs)
        self.pages = [
            "/", "/home", "/products", "/pricing",
            "/about", "/contact", "/blog", "/docs",
            "/api", "/dashboard", "/settings", "/profile",
            "/search", "/help", "/faq", "/download",
            "/login", "/register", "/checkout", "/cart"
        ]
        
        # HTTP methods
        self.http_methods = ["GET", "POST", "PUT", "DELETE"]
        self.method_weights = [0.70, 0.20, 0.05, 0.05]
        
        # HTTP status codes
        self.status_codes = [200, 201, 301, 304, 400, 403, 404, 500]
        self.status_weights = [0.70, 0.05, 0.03, 0.07, 0.05, 0.03, 0.05, 0.02]
        
        # User agents (trình duyệt)
        self.user_agents = [
            "Chrome/120.0", "Firefox/121.0", "Safari/17.2",
            "Edge/120.0", "Opera/105.0", "Mobile-Chrome/120.0",
            "Mobile-Safari/17.2"
        ]
    
    # =================================================================
    # PHẦN 1: Tạo Subscribers (Site A)
    # =================================================================
    
    def generate_subscribers(self, num_subscribers=10000):
        """
        Tạo bảng Subscribers cho Site A.
        
        Schema:
        ┌──────────────┬─────────────┬───────────────────┬──────────┬──────────────┐
        │ user_id (PK) │ full_name   │ email             │ plan     │ monthly_fee  │
        ├──────────────┼─────────────┼───────────────────┼──────────┼──────────────┤
        │ USR_00001    │ Nguyễn An   │ an.nguyen@mail... │ Premium  │ 399000       │
        │ USR_00002    │ Trần Bình   │ binh.tran@mail... │ Basic    │ 99000        │
        │ ...          │ ...         │ ...               │ ...      │ ...          │
        └──────────────┴─────────────┴───────────────────┴──────────┴──────────────┘
        
        Parameters:
            num_subscribers (int): Số lượng thuê bao cần tạo
            
        Returns:
            pd.DataFrame: Bảng Subscribers
        """
        print(f"\n[DataGenerator] Đang tạo {num_subscribers:,} Subscribers...")
        
        subscribers = []
        
        for i in range(1, num_subscribers + 1):
            # Tạo User ID có format cố định: USR_00001, USR_00002, ...
            user_id = f"USR_{i:05d}"
            
            # Chọn tên ngẫu nhiên
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            full_name = f"{last_name} {first_name}"
            
            # Tạo email từ tên (đơn giản hoá, không cần unique)
            email = f"{first_name.lower()}.{last_name.lower()}_{i}@mail.vn"
            
            # Chọn gói dịch vụ theo phân bổ (weighted random)
            plan_name, monthly_fee = random.choices(
                self.plans, weights=self.plan_weights, k=1
            )[0]
            
            # Ngày đăng ký (trong 2 năm gần đây)
            days_ago = random.randint(1, 730)
            register_date = (
                datetime(2026, 1, 1) - timedelta(days=days_ago)
            ).strftime("%Y-%m-%d")
            
            subscribers.append({
                'user_id': user_id,
                'full_name': full_name,
                'email': email,
                'plan': plan_name,
                'monthly_fee': monthly_fee,
                'register_date': register_date
            })
        
        df = pd.DataFrame(subscribers)
        
        # In thống kê
        print(f"  ✅ Đã tạo {len(df):,} subscribers")
        print(f"  📊 Phân bổ gói dịch vụ:")
        plan_counts = df['plan'].value_counts()
        for plan, count in plan_counts.items():
            pct = count / len(df) * 100
            print(f"     - {plan}: {count:,} ({pct:.1f}%)")
        print(f"  💰 Doanh thu tháng ước tính: "
              f"{df['monthly_fee'].sum():,.0f} VNĐ")
        
        return df
    
    # =================================================================
    # PHẦN 2: Tạo WebLogs (Site B)
    # =================================================================
    
    def generate_web_logs(self, num_logs=50000, 
                          subscriber_ids=None, 
                          overlap_ratio=0.35):
        """
        Tạo bảng WebLogs cho Site B.
        
        Thiết kế dữ liệu:
        - overlap_ratio (vd: 0.35 = 35%): Tỷ lệ logs thuộc về subscribers
        - 1 - overlap_ratio (65%): Logs từ guest users (không phải thuê bao)
        
        Ý nghĩa trong thực tế:
        → Website có cả khách vãng lai (guest) lẫn thuê bao (subscriber)
        → Khi JOIN, ta chỉ cần logs của subscribers
        → 65% logs là DƯ THỪA nếu gửi qua mạng
        → Bloom Filter giúp LỌC BỎ 65% dư thừa này TẠI Site B
        
        Schema:
        ┌────────────┬──────────────┬─────────┬────────┬────────┬────────────┐
        │ log_id(PK) │ user_id (FK) │ page    │ method │ status │ timestamp  │
        ├────────────┼──────────────┼─────────┼────────┼────────┼────────────┤
        │ LOG_000001 │ USR_00042    │ /home   │ GET    │ 200    │ 2026-01... │
        │ LOG_000002 │ GUEST_00531  │ /about  │ GET    │ 200    │ 2026-01... │
        │ ...        │ ...          │ ...     │ ...    │ ...    │ ...        │
        └────────────┴──────────────┴─────────┴────────┴────────┴────────────┘
        
        Parameters:
            num_logs (int): Tổng số bản ghi log cần tạo
            subscriber_ids (list): Danh sách user_id của subscribers (từ Site A)
            overlap_ratio (float): Tỷ lệ logs match với subscribers (0.0 - 1.0)
            
        Returns:
            pd.DataFrame: Bảng WebLogs
        """
        print(f"\n[DataGenerator] Đang tạo {num_logs:,} WebLogs "
              f"(overlap = {overlap_ratio:.0%})...")
        
        if subscriber_ids is None:
            # Nếu không có danh sách subscriber, tạo mặc định
            subscriber_ids = [f"USR_{i:05d}" for i in range(1, 10001)]
        
        # Tính số logs match vs không match
        num_matching = int(num_logs * overlap_ratio)
        num_guest = num_logs - num_matching
        
        logs = []
        
        # --- Phần 1: Logs từ SUBSCRIBERS (matching) ---
        # Chọn ngẫu nhiên một tập con subscribers (không phải tất cả đều truy cập)
        active_subscribers = random.sample(
            subscriber_ids, 
            min(len(subscriber_ids), int(len(subscriber_ids) * 0.6))
        )
        
        for i in range(num_matching):
            log_id = f"LOG_{i + 1:06d}"
            # Chọn ngẫu nhiên một subscriber đang hoạt động
            user_id = random.choice(active_subscribers)
            logs.append(self._create_log_entry(log_id, user_id))
        
        # --- Phần 2: Logs từ GUEST users (non-matching) ---
        for i in range(num_guest):
            log_id = f"LOG_{num_matching + i + 1:06d}"
            # Tạo Guest ID (KHÔNG có trong danh sách subscribers)
            guest_id = f"GUEST_{i + 1:05d}"
            logs.append(self._create_log_entry(log_id, guest_id))
        
        # Xáo trộn thứ tự logs (mô phỏng thực tế)
        random.shuffle(logs)
        
        df = pd.DataFrame(logs)
        
        # In thống kê
        subscriber_logs = df[df['user_id'].str.startswith('USR_')]
        guest_logs = df[df['user_id'].str.startswith('GUEST_')]
        
        print(f"  ✅ Đã tạo {len(df):,} web logs")
        print(f"  📊 Phân bổ:")
        print(f"     - Subscriber logs (match): {len(subscriber_logs):,} "
              f"({len(subscriber_logs)/len(df)*100:.1f}%)")
        print(f"     - Guest logs (no match):   {len(guest_logs):,} "
              f"({len(guest_logs)/len(df)*100:.1f}%)")
        print(f"  👥 Unique subscribers truy cập: "
              f"{subscriber_logs['user_id'].nunique():,}")
        print(f"  📄 Trang được truy cập nhiều nhất: "
              f"{df['page'].value_counts().index[0]}")
        
        # Tính kích thước dữ liệu
        total_size = df.memory_usage(deep=True).sum()
        print(f"  💾 Kích thước DataFrame: {total_size:,.0f} bytes "
              f"({total_size/1024:.1f} KB)")
        
        return df
    
    def _create_log_entry(self, log_id, user_id):
        """
        Tạo một bản ghi log đơn lẻ.
        
        Parameters:
            log_id (str): ID của bản ghi
            user_id (str): ID người dùng (subscriber hoặc guest)
            
        Returns:
            dict: Một bản ghi log
        """
        # Chọn trang, method, status theo phân bổ thực tế
        page = random.choice(self.pages)
        method = random.choices(
            self.http_methods, weights=self.method_weights, k=1
        )[0]
        status = random.choices(
            self.status_codes, weights=self.status_weights, k=1
        )[0]
        
        # Thời gian truy cập (trong 30 ngày gần đây)
        seconds_ago = random.randint(0, 30 * 24 * 3600)
        timestamp = (
            datetime(2026, 5, 1) - timedelta(seconds=seconds_ago)
        ).strftime("%Y-%m-%d %H:%M:%S")
        
        # Response time (ms) - phân bổ log-normal (giống thực tế)
        response_time = round(random.lognormvariate(4.5, 0.8), 2)
        
        # User agent
        user_agent = random.choice(self.user_agents)
        
        # Kích thước response (bytes)
        response_size = random.randint(500, 50000)
        
        return {
            'log_id': log_id,
            'user_id': user_id,
            'page': page,
            'method': method,
            'status_code': status,
            'response_time_ms': response_time,
            'response_size_bytes': response_size,
            'user_agent': user_agent,
            'timestamp': timestamp
        }
    
    # =================================================================
    # PHẦN 3: Phân tích dữ liệu đã tạo
    # =================================================================
    
    def analyze_data(self, subscribers_df, logs_df):
        """
        Phân tích chi tiết dữ liệu hai site.
        
        Tính toán:
        - Actual overlap: Bao nhiêu log thực sự match
        - Bandwidth waste: Bao nhiêu dữ liệu lãng phí nếu gửi hết
        - Potential savings: Bloom Filter có thể tiết kiệm bao nhiêu
        
        Parameters:
            subscribers_df: DataFrame Subscribers (Site A)
            logs_df: DataFrame WebLogs (Site B)
            
        Returns:
            dict: Kết quả phân tích
        """
        print(f"\n{'='*60}")
        print(f"  📊 PHÂN TÍCH DỮ LIỆU PHÂN TÁN")
        print(f"{'='*60}")
        
        # Tập user_id từ mỗi site
        subscriber_ids = set(subscribers_df['user_id'])
        log_user_ids = set(logs_df['user_id'])
        
        # Tính overlap (giao giữa 2 tập)
        overlap_ids = subscriber_ids & log_user_ids
        
        # Logs match với subscribers
        matching_logs = logs_df[logs_df['user_id'].isin(subscriber_ids)]
        non_matching_logs = logs_df[~logs_df['user_id'].isin(subscriber_ids)]
        
        # Kích thước dữ liệu
        total_log_size = logs_df.memory_usage(deep=True).sum()
        matching_log_size = matching_logs.memory_usage(deep=True).sum()
        non_matching_log_size = non_matching_logs.memory_usage(deep=True).sum()
        
        # Ước tính kích thước khi serialize (thực tế hơn)
        # Giả sử mỗi row ~ 150 bytes khi serialize
        bytes_per_row = 150
        total_transfer_naive = len(logs_df) * bytes_per_row
        actual_needed = len(matching_logs) * bytes_per_row
        wasted = total_transfer_naive - actual_needed
        
        print(f"\n  📋 Site A - Subscribers:")
        print(f"     - Tổng subscribers: {len(subscribers_df):,}")
        print(f"     - Unique user_ids:  {len(subscriber_ids):,}")
        
        print(f"\n  📋 Site B - WebLogs:")
        print(f"     - Tổng log entries:    {len(logs_df):,}")
        print(f"     - Unique user_ids:     {len(log_user_ids):,}")
        print(f"     - Logs match (cần):    {len(matching_logs):,} "
              f"({len(matching_logs)/len(logs_df)*100:.1f}%)")
        print(f"     - Logs no match (thừa): {len(non_matching_logs):,} "
              f"({len(non_matching_logs)/len(logs_df)*100:.1f}%)")
        
        print(f"\n  🔗 Overlap:")
        print(f"     - User IDs chung: {len(overlap_ids):,}")
        print(f"     - Overlap ratio:  "
              f"{len(overlap_ids)/len(log_user_ids)*100:.1f}% "
              f"(trong tổng unique log users)")
        
        print(f"\n  📡 Bandwidth Analysis (Naive JOIN - gửi hết):")
        print(f"     - Tổng dữ liệu gửi: "
              f"{total_transfer_naive:,} bytes "
              f"({total_transfer_naive/1024:.1f} KB)")
        print(f"     - Dữ liệu thực cần:  "
              f"{actual_needed:,} bytes "
              f"({actual_needed/1024:.1f} KB)")
        print(f"     - Lãng phí:          "
              f"{wasted:,} bytes "
              f"({wasted/1024:.1f} KB)")
        print(f"     - Tỷ lệ lãng phí:   "
              f"{wasted/total_transfer_naive*100:.1f}%")
        
        print(f"\n  💡 Bloom Filter có thể giúp loại bỏ ~"
              f"{wasted/total_transfer_naive*100:.0f}% dữ liệu thừa!")
        
        analysis = {
            'num_subscribers': len(subscribers_df),
            'num_logs': len(logs_df),
            'num_matching_logs': len(matching_logs),
            'num_non_matching_logs': len(non_matching_logs),
            'overlap_user_ids': len(overlap_ids),
            'total_transfer_naive_bytes': total_transfer_naive,
            'actual_needed_bytes': actual_needed,
            'wasted_bytes': wasted,
            'waste_ratio': wasted / total_transfer_naive,
            'subscriber_ids': subscriber_ids,
            'matching_logs': matching_logs,
            'non_matching_logs': non_matching_logs
        }
        
        return analysis
    
    # =================================================================
    # PHẦN 4: Tạo dữ liệu với các cấu hình khác nhau
    # =================================================================
    
    def generate_scenario(self, scenario_name, 
                          num_subscribers, num_logs, overlap_ratio):
        """
        Tạo một kịch bản dữ liệu hoàn chỉnh.
        
        Mỗi kịch bản bao gồm:
        1. Bảng Subscribers (Site A)
        2. Bảng WebLogs (Site B) với overlap_ratio đã định
        3. Phân tích chi tiết
        
        Parameters:
            scenario_name (str): Tên kịch bản (để hiển thị)
            num_subscribers (int): Số subscribers
            num_logs (int): Số web logs
            overlap_ratio (float): Tỷ lệ logs match (0.0 - 1.0)
            
        Returns:
            tuple: (subscribers_df, logs_df, analysis)
        """
        print(f"\n{'#'*65}")
        print(f"  KỊCH BẢN: {scenario_name}")
        print(f"  Subscribers: {num_subscribers:,} | "
              f"Logs: {num_logs:,} | "
              f"Overlap: {overlap_ratio:.0%}")
        print(f"{'#'*65}")
        
        # Tạo dữ liệu
        subscribers_df = self.generate_subscribers(num_subscribers)
        subscriber_ids = subscribers_df['user_id'].tolist()
        
        logs_df = self.generate_web_logs(
            num_logs=num_logs,
            subscriber_ids=subscriber_ids,
            overlap_ratio=overlap_ratio
        )
        
        # Phân tích
        analysis = self.analyze_data(subscribers_df, logs_df)
        
        return subscribers_df, logs_df, analysis


# =================================================================
# DEMO: Tạo và phân tích dữ liệu
# =================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO: Data Generator - Tạo Dữ Liệu Phân Tán")
    print("=" * 65)
    
    gen = DataGenerator(seed=42)
    
    # ----- Demo 1: Kịch bản mặc định -----
    print("\n📌 Demo 1: Kịch bản tiêu chuẩn")
    subscribers, logs, analysis = gen.generate_scenario(
        scenario_name="Tiêu chuẩn",
        num_subscribers=10000,
        num_logs=50000,
        overlap_ratio=0.35
    )
    
    # Hiển thị mẫu dữ liệu
    print(f"\n  📋 Mẫu Subscribers (5 dòng đầu):")
    print(subscribers.head().to_string(index=False))
    
    print(f"\n  📋 Mẫu WebLogs (5 dòng đầu):")
    print(logs.head().to_string(index=False))
    
    # ----- Demo 2: So sánh các kịch bản -----
    print(f"\n\n📌 Demo 2: So sánh kịch bản overlap khác nhau")
    print("-" * 60)
    
    scenarios = [
        ("Low Overlap (10%)", 5000, 30000, 0.10),
        ("Medium Overlap (35%)", 5000, 30000, 0.35),
        ("High Overlap (70%)", 5000, 30000, 0.70),
        ("Very High Overlap (90%)", 5000, 30000, 0.90),
    ]
    
    results = []
    for name, n_sub, n_log, overlap in scenarios:
        gen_temp = DataGenerator(seed=42)
        _, _, analysis_temp = gen_temp.generate_scenario(
            name, n_sub, n_log, overlap
        )
        results.append({
            'Scenario': name,
            'Match Logs': f"{analysis_temp['num_matching_logs']:,}",
            'Waste %': f"{analysis_temp['waste_ratio']*100:.1f}%",
            'Wasted KB': f"{analysis_temp['wasted_bytes']/1024:.1f}"
        })
    
    print(f"\n\n{'='*65}")
    print("  📊 BẢNG SO SÁNH CÁC KỊCH BẢN")
    print(f"{'='*65}")
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    print(f"\n  💡 Nhận xét:")
    print(f"     - Overlap càng THẤP → Lãng phí càng NHIỀU")
    print(f"     - Bloom Filter hiệu quả nhất khi overlap thấp")
    print(f"     - Overlap 10%: ~90% dữ liệu gửi là thừa!")
    
    print("\n" + "=" * 65)
    print("  ✅ Data Generator hoạt động chính xác!")
    print("=" * 65)
