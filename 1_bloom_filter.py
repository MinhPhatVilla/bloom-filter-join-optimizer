"""
==========================================================================
FILE 1: BLOOM FILTER - Cài đặt từ Scratch
==========================================================================
Môn: Cơ Sở Dữ Liệu Phân Tán
Đề tài: Bloom Filter Join Optimizer - "Subscribers & Logs"

Bloom Filter là cấu trúc dữ liệu XÁC SUẤT (probabilistic data structure)
dùng để kiểm tra "phần tử có thuộc tập hợp hay không" một cách NHANH và
TIẾT KIỆM BỘ NHỚ.

Đặc điểm quan trọng:
  - FALSE NEGATIVE = 0% → Không bao giờ bỏ sót phần tử thực sự có
  - FALSE POSITIVE > 0% → Có thể nhầm phần tử không có thành có
  
Ứng dụng trong CSDL phân tán:
  Site A tạo Bloom Filter từ UserIDs → gửi sang Site B
  Site B lọc WebLogs qua Bloom Filter → chỉ gửi rows match về Site A
  → Tiết kiệm bandwidth truyền tải dữ liệu giữa các site
==========================================================================
"""

import math
import mmh3  # MurmurHash3 - hàm băm nhanh, phân bố đều (thư viện hash, KHÔNG phải thư viện Bloom Filter)
from bitarray import bitarray  # Mảng bit hiệu quả về bộ nhớ


class BloomFilter:
    """
    Bloom Filter cài đặt từ scratch.
    
    Cấu trúc bên trong:
    ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
    │ 0 │ 0 │ 1 │ 0 │ 1 │ 0 │ 0 │ 1 │ 0 │ 0 │  ← bit array (m bits)
    └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
    
    Hai cách khởi tạo:
    1. Chỉ định trực tiếp m (kích thước bit array) và k (số hàm băm)
    2. Chỉ định n (số phần tử) và fp_rate (tỷ lệ false positive mong muốn)
       → Tự động tính m và k tối ưu
    """
    
    def __init__(self, size_m=None, num_hashes_k=None, 
                 expected_items_n=None, fp_rate=None):
        """
        Khởi tạo Bloom Filter.
        
        Parameters:
        -----------
        size_m : int, optional
            Kích thước bit array (số bits). Dùng khi muốn chỉ định trực tiếp.
        num_hashes_k : int, optional
            Số hàm băm. Dùng khi muốn chỉ định trực tiếp.
        expected_items_n : int, optional
            Số phần tử dự kiến sẽ insert. Dùng để tính m, k tối ưu.
        fp_rate : float, optional
            Tỷ lệ false positive mong muốn (ví dụ: 0.01 = 1%). 
            Dùng cùng expected_items_n để tính m, k tối ưu.
        """
        
        if expected_items_n is not None and fp_rate is not None:
            # =============================================
            # CÁCH 1: Tự động tính m và k từ n và fp_rate
            # =============================================
            # Công thức tính m tối ưu:
            #   m = -(n * ln(fp_rate)) / (ln2)^2
            #
            # Giải thích: Từ công thức FPR = (1 - e^(-kn/m))^k
            # Với k tối ưu, ta đạo hàm và giải ra m
            self.n = expected_items_n
            self.fp_rate = fp_rate
            self.m = self._optimal_size(expected_items_n, fp_rate)
            self.k = self._optimal_hash_count(self.m, expected_items_n)
            
        elif size_m is not None and num_hashes_k is not None:
            # =============================================
            # CÁCH 2: Chỉ định trực tiếp m và k
            # =============================================
            self.m = size_m
            self.k = num_hashes_k
            self.n = None
            self.fp_rate = None
            
        else:
            raise ValueError(
                "Phải cung cấp (size_m, num_hashes_k) "
                "hoặc (expected_items_n, fp_rate)"
            )
        
        # Khởi tạo bit array với tất cả bit = 0
        self.bit_array = bitarray(self.m)
        self.bit_array.setall(0)
        
        # Đếm số phần tử đã insert (để tính fill ratio)
        self.items_inserted = 0
        
        print(f"[Bloom Filter] Đã khởi tạo:")
        print(f"  - Kích thước bit array (m): {self.m:,} bits "
              f"({self.m / 8:,.0f} bytes = {self.m / 8 / 1024:,.2f} KB "
              f"= {self.m / 8 / 1024 / 1024:,.4f} MB)")
        print(f"  - Số hàm băm (k): {self.k}")
        if self.fp_rate:
            print(f"  - FPR mong muốn: {self.fp_rate * 100:.2f}%")
    
    # =================================================================
    # PHẦN 1: Tính toán tham số tối ưu
    # =================================================================
    
    @staticmethod
    def _optimal_size(n, fp_rate):
        """
        Tính kích thước bit array tối ưu.
        
        Công thức: m = -(n * ln(fp_rate)) / (ln2)^2
        
        Chứng minh:
        - FPR ≈ (1 - e^(-kn/m))^k
        - Với k = (m/n) * ln2, FPR được tối thiểu hoá
        - Giải phương trình FPR = p, ta được m = -(n * ln(p)) / (ln2)^2
        
        Parameters:
            n: Số phần tử dự kiến
            fp_rate: Tỷ lệ false positive mong muốn
            
        Returns:
            int: Kích thước bit array tối ưu (m)
        """
        m = -(n * math.log(fp_rate)) / (math.log(2) ** 2)
        return int(math.ceil(m))  # Làm tròn lên
    
    @staticmethod
    def _optimal_hash_count(m, n):
        """
        Tính số hàm băm tối ưu.
        
        Công thức: k = (m/n) * ln(2) ≈ 0.693 * (m/n)
        
        Chứng minh:
        - Để minimize FPR, ta lấy đạo hàm FPR theo k và cho = 0
        - Kết quả: k_opt = (m/n) * ln(2)
        
        Trực giác: 
        - k quá nhỏ → ít bit được set → chưa tận dụng hết bit array
        - k quá lớn → quá nhiều bit được set → tăng collision → tăng FPR
        - k tối ưu → cân bằng giữa hai thái cực
        
        Parameters:
            m: Kích thước bit array
            n: Số phần tử dự kiến
            
        Returns:
            int: Số hàm băm tối ưu (k)
        """
        k = (m / n) * math.log(2)
        return int(round(k))  # Làm tròn
    
    # =================================================================
    # PHẦN 2: Hàm băm (Hash Functions)
    # =================================================================
    
    def _get_hash_values(self, item):
        """
        Tính k giá trị hash cho một phần tử.
        
        Kỹ thuật: Double Hashing
        ========================
        Thay vì dùng k hàm băm độc lập (tốn tài nguyên),
        ta dùng kỹ thuật Double Hashing:
        
            h_i(x) = (h1(x) + i * h2(x)) % m
        
        Trong đó:
        - h1(x) = MurmurHash3 với seed = 0
        - h2(x) = MurmurHash3 với seed = 1  
        - i = 0, 1, 2, ..., k-1
        
        Bài báo chứng minh: Kirsch & Mitzenmacher (2006)
        "Less Hashing, Same Performance" → Double Hashing cho kết quả
        tương đương k hàm băm độc lập.
        
        Parameters:
            item: Phần tử cần hash (sẽ được chuyển thành string)
            
        Returns:
            list[int]: Danh sách k vị trí trong bit array
        """
        item_str = str(item)
        
        # Hai hàm băm cơ sở
        h1 = mmh3.hash(item_str, seed=0) % self.m
        h2 = mmh3.hash(item_str, seed=1) % self.m
        
        # Tạo k vị trí bằng Double Hashing
        positions = []
        for i in range(self.k):
            pos = (h1 + i * h2) % self.m
            # Đảm bảo vị trí không âm
            if pos < 0:
                pos += self.m
            positions.append(pos)
        
        return positions
    
    # =================================================================
    # PHẦN 3: Thao tác chính - INSERT và LOOKUP
    # =================================================================
    
    def insert(self, item):
        """
        Thêm một phần tử vào Bloom Filter.
        
        Quy trình:
        1. Tính k vị trí hash: h₁(item), h₂(item), ..., hₖ(item)
        2. Set các bit tại các vị trí đó = 1
        
        Ví dụ với m=16, k=3:
        ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
        │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │0 │ Trước
        └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
                  ↓ insert("user_123") → h1=2, h2=7, h3=13
        ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
        │0 │0 │1 │0 │0 │0 │0 │1 │0 │0 │0 │0 │0 │1 │0 │0 │ Sau
        └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
              ↑                 ↑                    ↑
              
        Parameters:
            item: Phần tử cần thêm
        """
        positions = self._get_hash_values(item)
        for pos in positions:
            self.bit_array[pos] = 1
        self.items_inserted += 1
    
    def lookup(self, item):
        """
        Kiểm tra phần tử có trong Bloom Filter không.
        
        Quy trình:
        1. Tính k vị trí hash
        2. Kiểm tra tất cả bit tại các vị trí đó
        
        Kết quả:
        - Nếu TẤT CẢ bit = 1 → "CÓ THỂ CÓ" (Maybe Yes)
          → Phần tử có thể trong tập hợp (hoặc là False Positive)
        - Nếu BẤT KỲ bit = 0 → "CHẮC CHẮN KHÔNG" (Definitely No)
          → Phần tử chắc chắn không trong tập hợp
        
        Parameters:
            item: Phần tử cần kiểm tra
            
        Returns:
            bool: True = "có thể có", False = "chắc chắn không"
        """
        positions = self._get_hash_values(item)
        for pos in positions:
            if self.bit_array[pos] == 0:
                return False  # Chắc chắn KHÔNG có
        return True  # CÓ THỂ có (hoặc False Positive)
    
    # =================================================================
    # PHẦN 4: Bulk operations - Insert và Lookup nhiều phần tử
    # =================================================================
    
    def bulk_insert(self, items):
        """
        Insert nhiều phần tử cùng lúc.
        
        Parameters:
            items: Iterable các phần tử cần insert
            
        Returns:
            int: Số phần tử đã insert
        """
        count = 0
        for item in items:
            self.insert(item)
            count += 1
        return count
    
    def bulk_lookup(self, items):
        """
        Lookup nhiều phần tử, trả về danh sách kết quả.
        
        Parameters:
            items: Iterable các phần tử cần kiểm tra
            
        Returns:
            tuple: (matches, non_matches) - hai danh sách phần tử
        """
        matches = []      # Phần tử "có thể có" trong BF
        non_matches = []   # Phần tử "chắc chắn không có"
        
        for item in items:
            if self.lookup(item):
                matches.append(item)
            else:
                non_matches.append(item)
        
        return matches, non_matches
    
    # =================================================================
    # PHẦN 5: Thống kê và phân tích
    # =================================================================
    
    def get_fill_ratio(self):
        """
        Tính tỷ lệ bit đã được set = 1 (fill ratio).
        
        Fill ratio cho biết Bloom Filter "đầy" đến mức nào:
        - Fill ratio thấp → ít collision → FPR thấp
        - Fill ratio cao → nhiều collision → FPR cao
        - Fill ratio = 50% → tối ưu (khi k = k_opt)
        
        Returns:
            float: Tỷ lệ bit = 1 (0.0 đến 1.0)
        """
        bits_set = self.bit_array.count(1)
        return bits_set / self.m
    
    def get_theoretical_fpr(self):
        """
        Tính tỷ lệ False Positive THEO LÝ THUYẾT.
        
        Công thức: FPR = (1 - e^(-kn/m))^k
        
        Giải thích từng phần:
        - e^(-kn/m): Xác suất một bit cụ thể vẫn = 0 sau khi insert n phần tử
        - (1 - e^(-kn/m)): Xác suất một bit cụ thể = 1
        - (...)^k: Xác suất cả k bit đều = 1 (giả sử độc lập)
        
        Returns:
            float: FPR lý thuyết (0.0 đến 1.0)
        """
        if self.items_inserted == 0:
            return 0.0
        
        n = self.items_inserted
        # FPR = (1 - e^(-kn/m))^k
        exponent = -self.k * n / self.m
        fpr = (1 - math.exp(exponent)) ** self.k
        return fpr
    
    def get_empirical_fpr(self, test_items, true_items_set):
        """
        Tính tỷ lệ False Positive THỰC TẾ bằng cách đo.
        
        So sánh kết quả Bloom Filter với tập hợp thực tế:
        - Nếu BF nói "có" nhưng thực tế "không có" → False Positive
        
        Parameters:
            test_items: Danh sách phần tử cần kiểm tra
            true_items_set: Set chứa các phần tử THỰC SỰ có
            
        Returns:
            dict: Thống kê chi tiết FP, TP, TN, FN
        """
        true_positives = 0   # BF nói "có", thực tế CÓ
        false_positives = 0  # BF nói "có", thực tế KHÔNG → Sai!
        true_negatives = 0   # BF nói "không", thực tế KHÔNG
        false_negatives = 0  # BF nói "không", thực tế CÓ → Không nên xảy ra!
        
        for item in test_items:
            bf_result = self.lookup(item)
            actually_exists = item in true_items_set
            
            if bf_result and actually_exists:
                true_positives += 1
            elif bf_result and not actually_exists:
                false_positives += 1
            elif not bf_result and not actually_exists:
                true_negatives += 1
            elif not bf_result and actually_exists:
                false_negatives += 1  # Lỗi! Không nên xảy ra
        
        total_negatives = false_positives + true_negatives
        empirical_fpr = false_positives / total_negatives if total_negatives > 0 else 0
        
        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives,  # Phải luôn = 0
            'empirical_fpr': empirical_fpr,
            'theoretical_fpr': self.get_theoretical_fpr(),
            'total_tested': len(test_items)
        }
    
    def get_size_bytes(self):
        """
        Trả về kích thước thực tế của Bloom Filter tính bằng bytes.
        
        Đây là kích thước dữ liệu cần truyền qua mạng trong 
        bài toán Semi-Join phân tán.
        
        Returns:
            int: Kích thước tính bằng bytes
        """
        return math.ceil(self.m / 8)
    
    def get_stats(self):
        """
        Trả về tất cả thông số thống kê của Bloom Filter.
        
        Returns:
            dict: Thống kê đầy đủ
        """
        return {
            'size_bits': self.m,
            'size_bytes': self.get_size_bytes(),
            'size_kb': self.get_size_bytes() / 1024,
            'size_mb': self.get_size_bytes() / (1024 * 1024),
            'num_hash_functions': self.k,
            'items_inserted': self.items_inserted,
            'fill_ratio': self.get_fill_ratio(),
            'theoretical_fpr': self.get_theoretical_fpr(),
            'bits_per_item': self.m / self.items_inserted if self.items_inserted > 0 else 0
        }
    
    def __repr__(self):
        """Hiển thị thông tin Bloom Filter."""
        return (
            f"BloomFilter(m={self.m:,}, k={self.k}, "
            f"items={self.items_inserted:,}, "
            f"fill={self.get_fill_ratio():.2%}, "
            f"FPR={self.get_theoretical_fpr():.4%})"
        )


# =================================================================
# DEMO: Kiểm tra Bloom Filter hoạt động đúng
# =================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO: Bloom Filter - Cài đặt từ Scratch")
    print("=" * 65)
    
    # ----- Demo 1: Tạo BF nhỏ để minh hoạ -----
    print("\n📌 Demo 1: Bloom Filter nhỏ (100 phần tử, FPR = 1%)")
    print("-" * 50)
    
    bf_small = BloomFilter(expected_items_n=100, fp_rate=0.01)
    
    # Insert 100 UserID
    for i in range(100):
        bf_small.insert(f"user_{i}")
    
    print(f"\nSau khi insert 100 phần tử:")
    print(f"  Fill ratio: {bf_small.get_fill_ratio():.2%}")
    print(f"  FPR lý thuyết: {bf_small.get_theoretical_fpr():.4%}")
    
    # Kiểm tra phần tử đã insert → phải trả về True
    print(f"\n  Lookup 'user_0': {bf_small.lookup('user_0')} (expect: True)")
    print(f"  Lookup 'user_50': {bf_small.lookup('user_50')} (expect: True)")
    print(f"  Lookup 'user_99': {bf_small.lookup('user_99')} (expect: True)")
    
    # Kiểm tra phần tử KHÔNG có → nên trả về False (nhưng có thể FP)
    print(f"  Lookup 'user_100': {bf_small.lookup('user_100')} (expect: False)")
    print(f"  Lookup 'user_999': {bf_small.lookup('user_999')} (expect: False)")
    
    # ----- Demo 2: Đo FPR thực tế -----
    print("\n\n📌 Demo 2: So sánh FPR lý thuyết vs thực tế")
    print("-" * 50)
    
    bf_test = BloomFilter(expected_items_n=10000, fp_rate=0.01)
    
    # Insert 10,000 phần tử
    true_items = set()
    for i in range(10000):
        item = f"member_{i}"
        bf_test.insert(item)
        true_items.add(item)
    
    # Test với 10,000 phần tử KHÔNG có trong BF
    test_items = [f"stranger_{i}" for i in range(10000)]
    
    results = bf_test.get_empirical_fpr(test_items, true_items)
    
    print(f"\n  Kết quả kiểm tra 10,000 phần tử không có trong BF:")
    print(f"  ├─ True Positives:  {results['true_positives']:,}")
    print(f"  ├─ False Positives: {results['false_positives']:,}")
    print(f"  ├─ True Negatives:  {results['true_negatives']:,}")
    print(f"  ├─ False Negatives: {results['false_negatives']:,} (phải = 0!)")
    print(f"  ├─ FPR lý thuyết:  {results['theoretical_fpr']:.4%}")
    print(f"  └─ FPR thực tế:    {results['empirical_fpr']:.4%}")
    
    # ----- Demo 3: Thống kê đầy đủ -----
    print("\n\n📌 Demo 3: Thống kê Bloom Filter")
    print("-" * 50)
    
    stats = bf_test.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:,.4f}")
        else:
            print(f"  {key}: {value:,}")
    
    # ----- Demo 4: Mô phỏng kích thước thực tế cho 1M UserIDs -----
    print("\n\n📌 Demo 4: Kích thước BF cho 1,000,000 UserIDs")
    print("-" * 50)
    
    for fpr in [0.1, 0.05, 0.01, 0.005, 0.001]:
        m = BloomFilter._optimal_size(1_000_000, fpr)
        k = BloomFilter._optimal_hash_count(m, 1_000_000)
        size_mb = m / 8 / 1024 / 1024
        print(f"  FPR = {fpr*100:5.1f}%  →  m = {m:>12,} bits "
              f"({size_mb:>6.2f} MB)  k = {k:>2}")
    
    print("\n" + "=" * 65)
    print("  ✅ Bloom Filter hoạt động chính xác!")
    print("=" * 65)
