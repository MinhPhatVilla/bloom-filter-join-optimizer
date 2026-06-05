"""
==========================================================================
FILE 3: SEMI-JOIN OPTIMIZER - Thuật Toán Tối Ưu Bằng Bloom Filter
==========================================================================
Môn: Cơ Sở Dữ Liệu Phân Tán
Đề tài: Bloom Filter Join Optimizer - "Subscribers & Logs"

File này mô phỏng quá trình thực thi truy vấn (Query Execution) trong 
môi trường phân tán.

Yêu cầu (Query):
  SELECT S.full_name, S.plan, W.page, W.timestamp
  FROM Subscribers S
  JOIN WebLogs W ON S.user_id = W.user_id

Hai chiến lược thực thi được so sánh:
1. NAIVE JOIN (Join Truyền Thống):
   - Chuyển toàn bộ dữ liệu WebLogs từ Site B sang Site A.
   - Thực hiện Join tại Site A.

2. BLOOM FILTER SEMI-JOIN (Join Tối Ưu):
   - Bước 1: Site A tạo Bloom Filter chứa user_id, gửi sang Site B.
   - Bước 2: Site B dùng Bloom Filter lọc bảng WebLogs.
   - Bước 3: Site B chỉ gửi những dòng WebLogs lọt qua màng lọc sang Site A.
   - Bước 4: Site A nhận dữ liệu và thực hiện Join cuối cùng.

Đo lường:
  - Lượng dữ liệu truyền tải (Network Bandwidth)
  - Số bản ghi xử lý (Processing Cost)
  - Ảnh hưởng của False Positive
==========================================================================
"""

import time
import pandas as pd
import importlib

# Workaround để import các file có tên bắt đầu bằng số
bloom_filter_mod = importlib.import_module("1_bloom_filter")
BloomFilter = bloom_filter_mod.BloomFilter

data_generator_mod = importlib.import_module("2_data_generator")
DataGenerator = data_generator_mod.DataGenerator

class DistributedJoinSimulator:
    """
    Trình mô phỏng quá trình Join giữa 2 site phân tán.
    """
    
    def __init__(self, subscribers_df, weblogs_df):
        """
        Khởi tạo simulator.
        
        Parameters:
            subscribers_df: DataFrame chứa thông tin thuê bao (ở Site A)
            weblogs_df: DataFrame chứa log truy cập (ở Site B)
        """
        self.site_a_data = subscribers_df
        self.site_b_data = weblogs_df
        
        # Giả định kích thước (đơn giản hoá để tính băng thông)
        self.BYTES_PER_LOG_ROW = 150  # Kích thước trung bình 1 dòng WebLog khi serialize
        self.BYTES_PER_ID = 10        # Kích thước 1 UserID khi gửi danh sách gốc
        
    # =================================================================
    # CHIẾN LƯỢC 1: NAIVE JOIN
    # =================================================================
    
    def run_naive_join(self):
        """
        Thực hiện chiến lược Naive Join (Gửi toàn bộ).
        
        Mô phỏng:
        1. Site B lấy toàn bộ WebLogs
        2. Truyền qua mạng (tính toán số bytes)
        3. Site A nhận và thực hiện Merge (Join)
        
        Returns:
            dict: Thống kê kết quả
        """
        print("\n[Chiến lược 1] Đang thực thi NAIVE JOIN (Gửi toàn bộ)...")
        start_time = time.time()
        
        # 1. Đoạn dữ liệu cần gửi từ Site B
        logs_to_transfer = self.site_b_data
        rows_transferred = len(logs_to_transfer)
        
        # 2. Tính toán băng thông truyền tải (Network Cost)
        network_bytes_transferred = rows_transferred * self.BYTES_PER_LOG_ROW
        
        # 3. Thực hiện Join tại Site A
        # (Dùng pd.merge để mô phỏng Hash Join / Merge Join trong DB)
        final_result = pd.merge(
            self.site_a_data, 
            logs_to_transfer, 
            on='user_id', 
            how='inner'
        )
        
        execution_time = time.time() - start_time
        
        return {
            'strategy': 'Naive Join',
            'rows_transferred': rows_transferred,
            'network_bytes': network_bytes_transferred,
            'final_rows': len(final_result),
            'execution_time_sec': execution_time,
            'false_positives': 0 # Không có FP vì gửi hết
        }

    # =================================================================
    # CHIẾN LƯỢC 2: BLOOM FILTER SEMI-JOIN
    # =================================================================
    
    def run_bloom_filter_semi_join(self, fpr_target=0.01):
        """
        Thực hiện chiến lược Semi-Join tối ưu bằng Bloom Filter.
        
        Mô phỏng:
        1. Site A: Quét danh sách user_id, tạo Bloom Filter
        2. Mạng: Truyền BF từ Site A -> Site B (Tính cost)
        3. Site B: Lọc WebLogs qua BF, loại bỏ các dòng chắc chắn KHÔNG phải của Site A
        4. Mạng: Truyền tập WebLogs đã lọc từ Site B -> Site A (Tính cost)
        5. Site A: Thực hiện Join cuối cùng để loại bỏ False Positive và lấy kết quả
        
        Parameters:
            fpr_target (float): Tỷ lệ False Positive mong muốn cho BF
            
        Returns:
            dict: Thống kê kết quả
        """
        print(f"\n[Chiến lược 2] Đang thực thi BF SEMI-JOIN (FPR = {fpr_target*100:.1f}%)...")
        start_time = time.time()
        
        # --- BƯỚC 1: TẠI SITE A ---
        # 1.1 Khởi tạo Bloom Filter
        num_subscribers = len(self.site_a_data)
        bf = BloomFilter(expected_items_n=num_subscribers, fp_rate=fpr_target)
        
        # 1.2 Insert toàn bộ user_id vào Bloom Filter
        # (Đây là thao tác quy mô nhỏ trên mem của Site A)
        user_ids = self.site_a_data['user_id'].tolist()
        bf.bulk_insert(user_ids)
        
        # --- BƯỚC 2: TRUYỀN TẢI A -> B ---
        # Gửi cấu trúc bit_array của Bloom Filter qua mạng
        bf_size_bytes = bf.get_size_bytes()
        
        # --- BƯỚC 3: TẠI SITE B ---
        # 3.1 Dùng Bloom Filter để lọc bảng WebLogs
        # (Đây là phép toán bộ nhớ siêu nhanh tại Site B)
        # Cách thực thi trong Pandas: dùng hàm apply kết hợp bf.lookup
        mask = self.site_b_data['user_id'].apply(lambda x: bf.lookup(x))
        
        # 3.2 Lấy ra những dòng "lọt qua màng lọc" (có thể chứa False Positive)
        filtered_logs = self.site_b_data[mask]
        rows_transferred = len(filtered_logs)
        
        # Đếm số lượng False Positives thực tế bị lọt qua (để thống kê, thực tế DB ko biết)
        # FP = Dòng lọt qua màng lọc nhưng user_id ko có ở Site A
        actual_subscribers_set = set(user_ids)
        false_positives = len(filtered_logs[~filtered_logs['user_id'].isin(actual_subscribers_set)])
        
        # --- BƯỚC 4: TRUYỀN TẢI B -> A ---
        # Tính kích thước dữ liệu WebLogs bị gửi về
        filtered_logs_bytes = rows_transferred * self.BYTES_PER_LOG_ROW
        
        # Tổng băng thông 2 chiều
        total_network_bytes = bf_size_bytes + filtered_logs_bytes
        
        # --- BƯỚC 5: TẠI SITE A (GIAI ĐOẠN CUỐI) ---
        # Join lần cuối để ra kết quả chuẩn xác 100%.
        # (Tại bước này, các dòng False Positive gửi nhầm từ Site B sẽ tự động bị loại bỏ
        # vì nó không khớp với bất kỳ user_id nào ở Site A).
        final_result = pd.merge(
            self.site_a_data, 
            filtered_logs, 
            on='user_id', 
            how='inner' # Inner join tự triệt tiêu False Positive
        )
        
        execution_time = time.time() - start_time

        # ==== METRIC CHÍNH CỦA ĐỀ BÀI ====
        # "Metric: Bytes saved vs. the size of the bit-vector (m bits)"
        naive_bytes_estimate = len(self.site_b_data) * self.BYTES_PER_LOG_ROW
        bytes_saved = naive_bytes_estimate - total_network_bytes
        # Savings leverage: cứ 1 byte BF → tiết kiệm được bao nhiêu bytes?
        savings_leverage = bytes_saved / bf_size_bytes if bf_size_bytes > 0 else 0
        # Bandwidth reduction ratio (đề bài gọi là "wasted bandwidth impact")
        wasted_bandwidth_naive = naive_bytes_estimate - (len(
            self.site_b_data[self.site_b_data['user_id'].isin(actual_subscribers_set)]
        ) * self.BYTES_PER_LOG_ROW)
        fp_extra_bytes = false_positives * self.BYTES_PER_LOG_ROW
        fpr_impact_on_bandwidth = fp_extra_bytes  # Số bytes thừa do FP gây ra

        return {
            'strategy': f'BF Semi-Join (FPR {fpr_target*100:.1f}%)',
            'fpr_target': fpr_target,
            'rows_transferred': rows_transferred,
            'bf_size_bytes': bf_size_bytes,
            'bf_size_bits': bf.m,                    # m bits - metric đề bài
            'num_hash_functions': bf.k,              # k hàm băm
            'payload_bytes': filtered_logs_bytes,
            'network_bytes': total_network_bytes,
            'bytes_saved': bytes_saved,              # KEY METRIC: Bytes saved
            'savings_leverage': savings_leverage,    # bytes saved per byte of BF
            'final_rows': len(final_result),
            'execution_time_sec': execution_time,
            'false_positives': false_positives,
            'fp_extra_bytes': fpr_impact_on_bandwidth  # Impact của FP lên bandwidth
        }
        
    # =================================================================
    # SO SÁNH & ĐÁNH GIÁ (EVALUATION)
    # =================================================================
    
    def compare_strategies(self):
        """
        Chạy đầy đủ tất cả chiến lược và in báo cáo đúng theo yêu cầu đề bài:
          - Bytes saved vs. the size of the bit-vector (m bits)
          - FPR impact on wasted bandwidth
        """
        print(f"\n{'='*72}")
        print(f"  BAT DAU MO PHONG THUC THI TRUY VAN PHAN TAN")
        print(f"{'='*72}")
        print(f"  Truy van: SELECT S.*, W.* FROM Subscribers S")
        print(f"            JOIN WebLogs W ON S.user_id = W.user_id")
        print(f"  - Site A (Subscribers): {len(self.site_a_data):>10,} dong")
        print(f"  - Site B (WebLogs):     {len(self.site_b_data):>10,} dong")
        print(f"  - Bytes/row (uoc tinh): {self.BYTES_PER_LOG_ROW} bytes")
        print(f"{'='*72}")

        results = []

        # 1. Chạy Naive Join
        res_naive = self.run_naive_join()
        results.append(res_naive)

        # 2. Chạy BF Join với 4 mức FPR
        for fpr in [0.10, 0.05, 0.01, 0.001]:
            res_bf = self.run_bloom_filter_semi_join(fpr_target=fpr)
            results.append(res_bf)

        naive_bytes = res_naive['network_bytes']
        naive_kb    = naive_bytes / 1024

        # ── BẢNG 1: Tổng quan băng thông ──────────────────────────────────────
        print(f"\n{'─'*72}")
        print(f"  BANG 1: SO SANH BANG THONG MANG")
        print(f"{'─'*72}")
        print(f"  {'Chien luoc':<26} {'Dong gui':>9} {'FP':>7} "
              f"{'Mang (KB)':>11} {'Tiet kiem':>10}")
        print(f"  {'─'*26} {'─'*9} {'─'*7} {'─'*11} {'─'*10}")

        for r in results:
            kb = r['network_bytes'] / 1024
            saving = (naive_kb - kb) / naive_kb * 100 if kb < naive_kb else 0
            saving_str = f"-{saving:.1f}%" if saving > 0 else "  baseline"
            fp = r['false_positives']
            print(f"  {r['strategy']:<26} {r['rows_transferred']:>9,} "
                  f"{fp:>7,} {kb:>11,.1f} {saving_str:>10}")

        # ── BẢNG 2: METRIC CHÍNH CỦA ĐỀ BÀI ──────────────────────────────────
        # "Metric: Bytes saved vs. the size of the bit-vector (m bits)"
        print(f"\n{'─'*72}")
        print(f"  BANG 2: BYTES SAVED vs. SIZE OF BIT-VECTOR (m bits)")
        print(f"  [Day la metric chinh theo yeu cau de bai]")
        print(f"{'─'*72}")
        print(f"  {'Chien luoc':<26} {'BF (m bits)':>12} {'BF (KB)':>9} "
              f"{'Saved (KB)':>11} {'Leverage':>10}")
        print(f"  {'─'*26} {'─'*12} {'─'*9} {'─'*11} {'─'*10}")

        for r in results:
            if 'bf_size_bits' not in r:
                # Naive Join: không có BF
                print(f"  {r['strategy']:<26} {'N/A':>12} {'N/A':>9} "
                      f"{'N/A':>11} {'N/A':>10}")
                continue
            m_bits   = r['bf_size_bits']
            bf_kb    = r['bf_size_bytes'] / 1024
            saved_kb = r['bytes_saved'] / 1024
            leverage = r['savings_leverage']
            print(f"  {r['strategy']:<26} {m_bits:>12,} {bf_kb:>9.2f} "
                  f"{saved_kb:>11,.1f} {leverage:>9.1f}x")

        print(f"\n  Giai thich cot 'Leverage': Cu 1 byte Bloom Filter -> tiet kiem duoc bao nhieu bytes")

        # ── BẢNG 3: Ảnh hưởng FPR lên bandwidth wasted ────────────────────────
        print(f"\n{'─'*72}")
        print(f"  BANG 3: ANH HUONG FPR LEN BANDWIDTH LANG PHI")
        print(f"  [Analysis: FPR impact on wasted bandwidth]")
        print(f"{'─'*72}")
        print(f"  {'Chien luoc':<26} {'FPR target':>11} {'FP rows':>9} "
              f"{'FP bytes (KB)':>14} {'k (hash)':>9}")
        print(f"  {'─'*26} {'─'*11} {'─'*9} {'─'*14} {'─'*9}")

        for r in results:
            if 'fpr_target' not in r:
                print(f"  {r['strategy']:<26} {'N/A':>11} {'0':>9} {'0':>14} {'N/A':>9}")
                continue
            fp_kb = r['fp_extra_bytes'] / 1024
            print(f"  {r['strategy']:<26} {r['fpr_target']*100:>10.1f}% "
                  f"{r['false_positives']:>9,} {fp_kb:>14.2f} "
                  f"{r['num_hash_functions']:>9}")

        # ── Kết luận ──────────────────────────────────────────────────────────
        best = min(results, key=lambda x: x['network_bytes'])
        best_saving_pct = (naive_kb - best['network_bytes']/1024) / naive_kb * 100

        print(f"\n{'='*72}")
        print(f"  KET LUAN:")
        print(f"{'='*72}")
        print(f"  [1] Ket qua Join: {res_naive['final_rows']:,} dong (chinh xac 100% - FP bi loai o Join cuoi)")
        print(f"  [2] Chien luoc tot nhat: {best['strategy']}")
        if 'bf_size_bits' in best:
            print(f"  [3] Kich thuoc Bloom Filter (m): {best['bf_size_bits']:,} bits "
                  f"= {best['bf_size_bytes']/1024:.2f} KB")
            print(f"  [4] Bytes saved vs BF size: {best['bytes_saved']/1024:,.1f} KB saved "
                  f"/ {best['bf_size_bytes']/1024:.2f} KB BF = {best['savings_leverage']:.1f}x leverage")
        print(f"  [5] Bandwidth: {naive_kb:,.1f} KB  =>  {best['network_bytes']/1024:,.1f} KB "
              f"(tiet kiem {best_saving_pct:.1f}%)")
        print(f"  [6] False Negative = 0% (TUYET DOI - BF khong bao gio bo sot subscriber)")
        print(f"{'='*72}")

        return results

# =================================================================
# MAIN EXECUTION
# =================================================================
if __name__ == "__main__":
    # 1. Sinh dữ liệu giả lập (Lấy kịch bản Low Overlap để thấy rõ sức mạnh BF)
    generator = DataGenerator(seed=999)
    subscribers, logs, analysis = generator.generate_scenario(
        scenario_name="Mô phỏng 10,000 Subs / 50,000 Logs (Overlap 20%)",
        num_subscribers=10000,
        num_logs=50000,
        overlap_ratio=0.20
    )
    
    # 2. Khởi tạo và chạy Simulator
    simulator = DistributedJoinSimulator(subscribers, logs)
    simulator.compare_strategies()
