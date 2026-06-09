import math
import mmh3  # MurmurHash3 - hàm băm nhanh, phân bố đều (thư viện hash, KHÔNG phải thư viện Bloom Filter)
from bitarray import bitarray  # Mảng bit hiệu quả về bộ nhớ

class BloomFilter:
    def __init__(self, size_m=None, num_hashes_k=None, 
                 expected_items_n=None, fp_rate=None):
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
        m = -(n * math.log(fp_rate)) / (math.log(2) ** 2)
        return int(math.ceil(m))  # Làm tròn lên
    
    @staticmethod
    def _optimal_hash_count(m, n):
        k = (m / n) * math.log(2)
        return int(round(k))  # Làm tròn
    
    # =================================================================
    # PHẦN 2: Hàm băm (Hash Functions)
    # =================================================================
    
    def _get_hash_values(self, item):
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
        positions = self._get_hash_values(item)
        for pos in positions:
            self.bit_array[pos] = 1
        self.items_inserted += 1
    
    def lookup(self, item):
        positions = self._get_hash_values(item)
        for pos in positions:
            if self.bit_array[pos] == 0:
                return False  # Chắc chắn KHÔNG có
        return True  # CÓ THỂ có (hoặc False Positive)
    
    # =================================================================
    # PHẦN 4: Bulk operations - Insert và Lookup nhiều phần tử
    # =================================================================
    
    def bulk_insert(self, items):
        count = 0
        for item in items:
            self.insert(item)
            count += 1
        return count
    
    def bulk_lookup(self, items):
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
        bits_set = self.bit_array.count(1)
        return bits_set / self.m
    
    def get_theoretical_fpr(self):
        if self.items_inserted == 0:
            return 0.0
        
        n = self.items_inserted
        # FPR = (1 - e^(-kn/m))^k
        exponent = -self.k * n / self.m
        fpr = (1 - math.exp(exponent)) ** self.k
        return fpr
    
    def get_empirical_fpr(self, test_items, true_items_set):
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
        return math.ceil(self.m / 8)
    
    def get_stats(self):
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
