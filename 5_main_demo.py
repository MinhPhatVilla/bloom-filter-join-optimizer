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
    In bao cao tong ket cuoi cung, bao gom day du metric theo de bai:
      - Bytes saved vs. the size of the bit-vector (m bits)
      - FPR impact on wasted bandwidth
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
    Tinh toan ly thuyet cho quy mo chinh xac cua de bai:
      - Subscribers (Site A): 1,000,000 rows
      - WebLogs     (Site B): 10,000,000 rows

    Vi may tinh ca nhan khong du RAM de thuc thi thuc te voi 10M rows,
    ta dung cong thuc Bloom Filter de tinh chinh xac cac con so ly thuyet.
    Ket qua nay HOAN TOAN CHINH XAC ve mat toan hoc.
  NHAN XET (Metric de bai: Bytes saved vs. size of bit-vector m bits):
  [1] Bloom Filter 1M subscribers, FPR=1%:
        m = {m1:,} bits = {bf1_mb:.2f} MB
        So voi gui danh sach ID thuan: 1M x 10 bytes = 10 MB -> BF nho hon ~{10/bf1_mb:.0f}x
  [2] Bytes SAVED (FPR=1%): ~{saved1/1024/1024:.0f} MB  /  BF ~{bf1_mb:.2f} MB = ~{saved1/((m1//8+1)):.0f}x leverage
  [3] FPR tang -> m nho, BF nhe, nhung FP nhieu -> gui nhieu data thua hon
  [4] FPR giam -> m lon, BF chinh xac hon, FP it -> bandwidth toi uu hon
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
