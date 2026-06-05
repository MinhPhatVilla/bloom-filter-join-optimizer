"""
==========================================================================
WEB APP: Flask Backend cho Bloom Filter Join Optimizer Dashboard
==========================================================================
Cung cấp API endpoints để frontend gọi và nhận kết quả JSON.

Cách chạy:
    python app.py
    → Mở trình duyệt: http://localhost:5000
==========================================================================
"""

import math
import time
import importlib
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template, jsonify, request

# Import các module đã tạo
bloom_mod = importlib.import_module("1_bloom_filter")
BloomFilter = bloom_mod.BloomFilter

datagen_mod = importlib.import_module("2_data_generator")
DataGenerator = datagen_mod.DataGenerator

semijoin_mod = importlib.import_module("3_semi_join")
DistributedJoinSimulator = semijoin_mod.DistributedJoinSimulator

app = Flask(__name__)


# =================================================================
# ROUTE: Trang chính
# =================================================================

@app.route('/')
def index():
    return render_template('index.html')


# =================================================================
# API: Chạy mô phỏng đầy đủ
# =================================================================

@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """
    Chạy toàn bộ pipeline Bloom Filter Semi-Join và trả về JSON.
    
    Body params (JSON):
        num_subscribers: int (default 10000)
        num_logs: int (default 50000)
        overlap_ratio: float (default 0.20)
    """
    try:
        data = request.get_json() or {}
        num_subscribers = int(data.get('num_subscribers', 10000))
        num_logs = int(data.get('num_logs', 50000))
        overlap_ratio = float(data.get('overlap_ratio', 0.20))
        
        # Giới hạn an toàn để tránh crash
        num_subscribers = min(num_subscribers, 200000)
        num_logs = min(num_logs, 2000000)
        overlap_ratio = max(0.05, min(0.95, overlap_ratio))
        
        t_start = time.time()
        
        # Bước 1: Tạo dữ liệu
        generator = DataGenerator(seed=2024)
        subscribers, logs, data_analysis = generator.generate_scenario(
            scenario_name="Web Demo",
            num_subscribers=num_subscribers,
            num_logs=num_logs,
            overlap_ratio=overlap_ratio
        )
        
        # Bước 2: Chạy simulation
        simulator = DistributedJoinSimulator(subscribers, logs)
        
        results = []
        
        # Naive Join
        r_naive = simulator.run_naive_join()
        results.append(r_naive)
        
        # BF Semi-Join với 4 mức FPR
        for fpr in [0.10, 0.05, 0.01, 0.001]:
            r_bf = simulator.run_bloom_filter_semi_join(fpr_target=fpr)
            results.append(r_bf)
        
        t_elapsed = time.time() - t_start
        
        # Chuẩn bị response JSON
        naive_bytes = results[0]['network_bytes']
        
        formatted_results = []
        for r in results:
            entry = {
                'strategy': r['strategy'],
                'rows_transferred': r['rows_transferred'],
                'network_bytes': r['network_bytes'],
                'network_kb': round(r['network_bytes'] / 1024, 2),
                'final_rows': r['final_rows'],
                'false_positives': r['false_positives'],
                'execution_time': round(r['execution_time_sec'], 3),
                'saving_pct': round((naive_bytes - r['network_bytes']) / naive_bytes * 100, 1) if r['network_bytes'] < naive_bytes else 0
            }
            
            # Thêm metric BF nếu có
            if 'bf_size_bits' in r:
                entry.update({
                    'bf_size_bits': r['bf_size_bits'],
                    'bf_size_bytes': r['bf_size_bytes'],
                    'bf_size_kb': round(r['bf_size_bytes'] / 1024, 2),
                    'num_hash_functions': r['num_hash_functions'],
                    'bytes_saved': r['bytes_saved'],
                    'bytes_saved_kb': round(r['bytes_saved'] / 1024, 2),
                    'savings_leverage': round(r['savings_leverage'], 1),
                    'fpr_target': r['fpr_target'],
                    'fp_extra_bytes': r['fp_extra_bytes'],
                    'fp_extra_kb': round(r['fp_extra_bytes'] / 1024, 2),
                })
            
            formatted_results.append(entry)
        
        response = {
            'success': True,
            'config': {
                'num_subscribers': num_subscribers,
                'num_logs': num_logs,
                'overlap_ratio': overlap_ratio,
            },
            'data_analysis': {
                'num_matching_logs': data_analysis['num_matching_logs'],
                'num_non_matching_logs': data_analysis['num_non_matching_logs'],
                'waste_ratio': round(data_analysis['waste_ratio'] * 100, 1),
            },
            'results': formatted_results,
            'elapsed_seconds': round(t_elapsed, 2)
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =================================================================
# API: Tính toán lý thuyết (nhanh, không cần tạo data)
# =================================================================

@app.route('/api/theoretical', methods=['POST'])
def theoretical_analysis():
    """
    Tính toán lý thuyết cho quy mô bất kỳ bằng công thức BF.
    Không cần tạo dữ liệu thực → phản hồi tức thì.
    """
    try:
        data = request.get_json() or {}
        n_subs = int(data.get('num_subscribers', 1_000_000))
        n_logs = int(data.get('num_logs', 10_000_000))
        overlap = float(data.get('overlap_ratio', 0.20))
        bytes_row = 150
        
        naive_bytes = n_logs * bytes_row
        
        theory_results = []
        for fpr in [0.10, 0.05, 0.01, 0.005, 0.001]:
            m = BloomFilter._optimal_size(n_subs, fpr)
            k = BloomFilter._optimal_hash_count(m, n_subs)
            bf_bytes = m // 8 + 1
            fp_rows = int(int(n_logs * (1 - overlap)) * fpr)
            rows_sent = int(n_logs * overlap) + fp_rows
            total_bytes = bf_bytes + rows_sent * bytes_row
            bytes_saved = naive_bytes - total_bytes
            saved_pct = bytes_saved / naive_bytes * 100
            leverage = bytes_saved / bf_bytes
            
            theory_results.append({
                'fpr': fpr,
                'fpr_pct': fpr * 100,
                'm_bits': m,
                'k': k,
                'bf_mb': round(bf_bytes / 1024 / 1024, 4),
                'total_mb': round(total_bytes / 1024 / 1024, 2),
                'saved_mb': round(bytes_saved / 1024 / 1024, 2),
                'saved_pct': round(saved_pct, 1),
                'leverage': round(leverage, 1),
                'fp_rows': fp_rows,
                'rows_sent': rows_sent,
            })
        
        return jsonify({
            'success': True,
            'config': {
                'num_subscribers': n_subs,
                'num_logs': n_logs,
                'overlap_ratio': overlap,
                'naive_mb': round(naive_bytes / 1024 / 1024, 2),
            },
            'results': theory_results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =================================================================
# API: Demo Bloom Filter đơn giản
# =================================================================

@app.route('/api/bloom-filter-demo', methods=['POST'])
def bloom_filter_demo():
    """
    Demo nhanh Bloom Filter: insert + lookup + FPR.
    """
    try:
        data = request.get_json() or {}
        n = int(data.get('num_items', 1000))
        fpr_target = float(data.get('fpr', 0.01))
        
        n = min(n, 100000)  # Giới hạn an toàn
        
        bf = BloomFilter(expected_items_n=n, fp_rate=fpr_target)
        
        # Insert items
        true_items = set()
        for i in range(n):
            item = f"user_{i}"
            bf.insert(item)
            true_items.add(item)
        
        # Test FPR với n items không có trong BF
        test_items = [f"stranger_{i}" for i in range(n)]
        fpr_result = bf.get_empirical_fpr(test_items, true_items)
        
        stats = bf.get_stats()
        
        return jsonify({
            'success': True,
            'stats': {
                'size_bits': stats['size_bits'],
                'size_kb': round(stats['size_kb'], 2),
                'num_hash_functions': stats['num_hash_functions'],
                'items_inserted': stats['items_inserted'],
                'fill_ratio': round(stats['fill_ratio'] * 100, 2),
                'bits_per_item': round(stats['bits_per_item'], 2),
            },
            'fpr': {
                'theoretical': round(fpr_result['theoretical_fpr'] * 100, 4),
                'empirical': round(fpr_result['empirical_fpr'] * 100, 4),
                'true_positives': fpr_result['true_positives'],
                'false_positives': fpr_result['false_positives'],
                'true_negatives': fpr_result['true_negatives'],
                'false_negatives': fpr_result['false_negatives'],
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =================================================================
# API: Dữ liệu cho biểu đồ BF size
# =================================================================

@app.route('/api/bf-size-data')
def bf_size_data():
    """Trả về dữ liệu BF size theo n và FPR cho biểu đồ."""
    import numpy as np
    
    n_values = list(range(1000, 1_000_001, 10000))
    fpr_list = [0.10, 0.05, 0.01, 0.001]
    
    datasets = {}
    for fpr in fpr_list:
        sizes = []
        for n in n_values:
            m = BloomFilter._optimal_size(n, fpr)
            sizes.append(round(m / 8 / 1024 / 1024, 4))
        datasets[f"FPR {fpr*100:.1f}%"] = sizes
    
    return jsonify({
        'n_values': [n / 1000 for n in n_values],  # in thousands
        'datasets': datasets
    })


# =================================================================
# MAIN
# =================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  BLOOM FILTER JOIN OPTIMIZER - Web Dashboard")
    print("  Open browser: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
