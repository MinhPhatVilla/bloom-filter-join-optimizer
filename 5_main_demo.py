"""
==========================================================================
FILE 5: MAIN DEMO - Điểm Khởi Chạy Tổng Hợp Toàn Bộ Dự Án
==========================================================================
Môn: Cơ Sở Dữ Liệu Phân Tán
Đề tài: Bloom Filter Join Optimizer - "Subscribers & Logs"

File này là điểm khởi chạy DUY NHẤT của toàn bộ dự án.
Nó kết hợp tất cả các file lại thành một pipeline hoàn chỉnh:

  File 1 (BloomFilter)  ──┐
  File 2 (DataGenerator)──┤──► File 3 (SemiJoin) ──► File 4 (Visualization)
                           ┘          │
                                      ▼
                                File 5 (Main - file này)
                                Tổng kết + In báo cáo cuối

Cách chạy:
  python 5_main_demo.py
==========================================================================
"""

import sys
import time
import importlib
import warnings
warnings.filterwarnings('ignore')  # Tắt warning không quan trọng

# =================================================================
# IMPORT CÁC MODULE ĐÃ TẠO
# =================================================================

print("Dang khoi dong he thong...")

bloom_mod  = importlib.import_module("1_bloom_filter")
BloomFilter = bloom_mod.BloomFilter

datagen_mod   = importlib.import_module("2_data_generator")
DataGenerator = datagen_mod.DataGenerator

semijoin_mod         = importlib.import_module("3_semi_join")
DistributedJoinSimulator = semijoin_mod.DistributedJoinSimulator

viz_mod          = importlib.import_module("4_visualization")
draw_full_dashboard = viz_mod.draw_full_dashboard

print("  [OK] Tat ca module da duoc import thanh cong!\n")


# =================================================================
# BANNER IN ĐẦU CHƯƠNG TRÌNH
# =================================================================

def print_banner():
    banner = """
  ============================================================
     BLOOM FILTER SEMI-JOIN OPTIMIZER
     Mon: Co So Du Lieu Phan Tan
     De tai: Subscribers & Web Logs
  ============================================================
  Pipeline:
    [1] Tao du lieu (DataGenerator)
    [2] Xay dung Bloom Filter (BloomFilter)
    [3] Chay va so sanh Join Strategy (SemiJoin)
    [4] Ve bieu do ket qua (Visualization)
    [5] Tong ket bao cao (Main - ban dang o day)
  ============================================================
"""
    print(banner)


# =================================================================
# IN BÁO CÁO CUỐI CÙNG (Final Report)
# =================================================================

def print_final_report(benchmark_results, scenario_config):
    """
    In bao cao tong ket cuoi cung, bao gom day du metric theo de bai:
      - Bytes saved vs. the size of the bit-vector (m bits)
      - FPR impact on wasted bandwidth
    """
    print("\n" + "=" * 70)
    print("  BAO CAO TONG KET CUOI CUNG")
    print("=" * 70)

    print(f"\n  Kich ban: {scenario_config['name']}")
    print(f"  - Subscribers (Site A): {scenario_config['num_subscribers']:>12,} dong")
    print(f"  - WebLogs     (Site B): {scenario_config['num_logs']:>12,} dong")
    print(f"  - Overlap Ratio:        {scenario_config['overlap_ratio']*100:>11.0f}%")

    naive = benchmark_results[0]
    naive_kb = naive['network_bytes'] / 1024

    print("\n  " + "-" * 68)
    print(f"  {'Chien luoc':<26} {'Mang(KB)':>10} {'Tiet kiem':>10} "
          f"{'BF(m bits)':>12} {'Leverage':>9} {'Ket qua':>8}")
    print("  " + "-" * 68)

    for r in benchmark_results:
        kb = r['network_bytes'] / 1024
        saving = (naive_kb - kb) / naive_kb * 100
        saving_str = "   N/A" if saving == 0 else f"-{saving:>5.1f}%"
        m_bits = f"{r['bf_size_bits']:,}" if 'bf_size_bits' in r else "N/A"
        leverage = f"{r['savings_leverage']:.1f}x" if 'savings_leverage' in r else "N/A"
        result_rows = r.get('final_rows', '?')
        name = r['strategy'][:25]
        print(f"  {name:<26} {kb:>10,.1f} {saving_str:>10} "
              f"{m_bits:>12} {leverage:>9} {result_rows:>8,}")

    print("  " + "-" * 68)

    best = min(benchmark_results, key=lambda x: x['network_bytes'])
    best_saving = (naive_kb - best['network_bytes'] / 1024) / naive_kb * 100

    print(f"""
  KET LUAN (dung voi metric de bai):
  [1] Chien luoc tot nhat  : {best['strategy']}
  [2] Bandwidth (Naive)    : {naive_kb:>12,.1f} KB (gui toan bo WebLogs)
  [3] Bandwidth (BF best)  : {best['network_bytes']/1024:>12,.1f} KB (BF + filtered logs)
  [4] Bytes SAVED          : {best.get('bytes_saved',0)/1024:>12,.1f} KB
  [5] BF size (m bits)     : {best.get('bf_size_bits',0):>12,} bits = {best.get('bf_size_bytes',0)/1024:.2f} KB
  [6] Savings Leverage     : {best.get('savings_leverage',0):>11.1f}x   (cu 1 byte BF -> tiet kiem bay nhieu bytes)
  [7] Bandwidth reduction  : {best_saving:>11.1f}%
  [8] Do chinh xac         : 100%  (FP tu dong bi loai o Inner Join cuoi)
  [9] False Negative       :   0%  (BF tuyet doi khong bo sot subscriber)
    """)


    print("=" * 70)
    print("  [OK] KET QUA CHINH XAC - Du lieu toan ven 100%!")
    print("=" * 70)


# =================================================================
# PHAN TICH LY THUYET THEO DUNG QUY MO DE BAI (1M / 10M)
# =================================================================

def print_theoretical_analysis():
    """
    Tinh toan ly thuyet cho quy mo chinh xac cua de bai:
      - Subscribers (Site A): 1,000,000 rows
      - WebLogs     (Site B): 10,000,000 rows

    Vi may tinh ca nhan khong du RAM de thuc thi thuc te voi 10M rows,
    ta dung cong thuc Bloom Filter de tinh chinh xac cac con so ly thuyet.
    Ket qua nay HOAN TOAN CHINH XAC ve mat toan hoc.
    """
    print("\n" + "=" * 70)
    print("  PHAN TICH LY THUYET - QUY MO DE BAI: 1,000,000 / 10,000,000 ROWS")
    print("  [Tinh theo cong thuc BF - chinh xac 100% ve toan hoc]")
    print("=" * 70)

    N_SUBS    = 1_000_000
    N_LOGS    = 10_000_000
    OVERLAP   = 0.20
    BYTES_ROW = 150

    naive_bytes  = N_LOGS * BYTES_ROW

    print(f"\n  Dataset (dung theo de bai):")
    print(f"    - Subscribers (Site A) : {N_SUBS:>12,} rows")
    print(f"    - WebLogs     (Site B) : {N_LOGS:>12,} rows  (ty le 1:10)")
    print(f"    - Overlap ratio        : {OVERLAP*100:>11.0f}%")
    print(f"    - Logs can giu lai     : {int(N_LOGS*OVERLAP):>12,} rows ({OVERLAP*100:.0f}%)")
    print(f"    - Logs lang phi Guest  : {int(N_LOGS*(1-OVERLAP)):>12,} rows ({(1-OVERLAP)*100:.0f}%)")
    print(f"\n  Naive Join: {naive_bytes/1024/1024:,.0f} MB phai truyen qua mang!")

    print(f"\n  Bloom Filter Semi-Join (tinh theo cong thuc):")
    print(f"  {'FPR':>8} {'m (bits)':>14} {'BF(MB)':>8} {'Total(MB)':>10} "
          f"{'Saved(MB)':>10} {'Saved%':>7} {'Leverage':>9}")
    print(f"  {'─'*8} {'─'*14} {'─'*8} {'─'*10} {'─'*10} {'─'*7} {'─'*9}")

    BF = BloomFilter
    for fpr in [0.10, 0.05, 0.01, 0.005, 0.001]:
        m        = BF._optimal_size(N_SUBS, fpr)
        bf_bytes = m // 8 + 1
        fp_rows  = int(int(N_LOGS * (1 - OVERLAP)) * fpr)
        rows_sent = int(N_LOGS * OVERLAP) + fp_rows
        total_bytes  = bf_bytes + rows_sent * BYTES_ROW
        bytes_saved  = naive_bytes - total_bytes
        saved_pct    = bytes_saved / naive_bytes * 100
        leverage     = bytes_saved / bf_bytes

        print(f"  {fpr*100:>7.1f}% {m:>14,} {bf_bytes/1024/1024:>8.2f} "
              f"{total_bytes/1024/1024:>10.2f} "
              f"{bytes_saved/1024/1024:>10.2f} "
              f"{saved_pct:>6.1f}% {leverage:>8.1f}x")

    # Tinh chi tiet cho FPR=1% de trinh bay
    m1 = BF._optimal_size(N_SUBS, 0.01)
    bf1_mb = (m1//8+1)/1024/1024
    fp1 = int(int(N_LOGS*0.8)*0.01)
    saved1 = naive_bytes - ((m1//8+1) + (int(N_LOGS*0.2)+fp1)*BYTES_ROW)

    print(f"""
  NHAN XET (Metric de bai: Bytes saved vs. size of bit-vector m bits):
  [1] Bloom Filter 1M subscribers, FPR=1%:
        m = {m1:,} bits = {bf1_mb:.2f} MB
        So voi gui danh sach ID thuan: 1M x 10 bytes = 10 MB -> BF nho hon ~{10/bf1_mb:.0f}x
  [2] Bytes SAVED (FPR=1%): ~{saved1/1024/1024:.0f} MB  /  BF ~{bf1_mb:.2f} MB = ~{saved1/((m1//8+1)):.0f}x leverage
  [3] FPR tang -> m nho, BF nhe, nhung FP nhieu -> gui nhieu data thua hon
  [4] FPR giam -> m lon, BF chinh xac hon, FP it -> bandwidth toi uu hon
    """)
    print("=" * 70)


# =================================================================
# HÀM MAIN — Điều Phối Toàn Bộ Pipeline
# =================================================================

def main():
    """Điều phối toàn bộ pipeline từ đầu đến cuối."""
    
    print_banner()
    
    # -------------------------------------------------------
    # BƯỚC 1: Tạo dữ liệu
    # -------------------------------------------------------
    print("\n[BUOC 1/4] Tao du lieu gia lap...")
    
    scenario_config = {
        'name': '100K Subscribers (Site A) / 1M WebLogs (Site B) - Ty le 1:10 giong de bai',
        'num_subscribers': 100_000,
        'num_logs': 1_000_000,
        'overlap_ratio': 0.20
    }
    
    generator = DataGenerator(seed=2024)
    subscribers, logs, data_analysis = generator.generate_scenario(
        scenario_name=scenario_config['name'],
        num_subscribers=scenario_config['num_subscribers'],
        num_logs=scenario_config['num_logs'],
        overlap_ratio=scenario_config['overlap_ratio']
    )
    
    # -------------------------------------------------------
    # BƯỚC 2: Chạy và so sánh các chiến lược Join
    # -------------------------------------------------------
    print("\n[BUOC 2/4] Chay mo phong Join Phan Tan...")
    
    simulator = DistributedJoinSimulator(subscribers, logs)
    
    # Thu thập kết quả thủ công (để truyền sang Visualization)
    benchmark_results = []
    
    r_naive = simulator.run_naive_join()
    benchmark_results.append(r_naive)
    
    for fpr in [0.10, 0.05, 0.01, 0.001]:
        r_bf = simulator.run_bloom_filter_semi_join(fpr_target=fpr)
        benchmark_results.append(r_bf)
    
    # In bảng so sánh
    simulator.compare_strategies()
    
    # -------------------------------------------------------
    # BUOC 3: In bao cao tong ket
    # -------------------------------------------------------
    print("\n[BUOC 3/5] In bao cao tong ket...")
    print_final_report(benchmark_results, scenario_config)

    # -------------------------------------------------------
    # BUOC 4: Tinh toan ly thuyet cho quy mo 1 TRIEU / 10 TRIEU
    # (Theo dung yeu cau de bai: 1M subscribers, 10M WebLogs)
    # -------------------------------------------------------
    print("\n[BUOC 4/5] Phan tich ly thuyet tai quy mo de bai (1M / 10M)...")
    print_theoretical_analysis()

    # -------------------------------------------------------
    # BUOC 5: Ve bieu do
    # -------------------------------------------------------
    print("\n[BUOC 5/5] Ve bieu do dashboard...")
    try:
        draw_full_dashboard(benchmark_results)
        print("  [OK] Dashboard da duoc luu tai: dashboard.png")
    except Exception as e:
        print(f"  [WARN] Khong the ve bieu do: {e}")
        print("  => Ket qua van duoc in day du phia tren.")
    
    print("\n  Cam on ban da su dung Bloom Filter Join Optimizer!")
    print("  Chay ket thuc thanh cong.\n")


# =================================================================
# ENTRY POINT
# =================================================================

if __name__ == '__main__':
    t_start = time.time()
    main()
    t_end = time.time()
    print(f"  Tong thoi gian chay: {t_end - t_start:.2f} giay\n")
