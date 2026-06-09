import sys
import os
import io
import json
import math
import time
import importlib
import warnings
warnings.filterwarnings('ignore')

# Cấu hình stdout/stderr dùng UTF-8 trên Windows để tránh lỗi charmap codec khi in tiếng Việt
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

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
    try:
        data = request.get_json() or {}
        num_subscribers = int(data.get('num_subscribers', 10000))
        num_logs = int(data.get('num_logs', 50000))
        overlap_ratio = float(data.get('overlap_ratio', 0.20))
        node_b_online = data.get('node_b_online', True)
        
        # Nếu Node B bị offline, mô phỏng sập mạng kết nối với Node B
        if not node_b_online:
            time.sleep(1.2)  # Mô phỏng độ trễ mạng trước khi timeout
            return jsonify({
                'success': False,
                'error': 'Connection timed out: Node B (Web Server Site) is unreachable. Distributed transaction aborted.'
            }), 504
            
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
# API: Phân tích điểm gãy Break-even Point
# =================================================================

@app.route('/api/breakeven-analysis', methods=['POST'])
def breakeven_analysis():
    try:
        data = request.get_json() or {}
        n_subs = int(data.get('num_subscribers', 10000))
        n_logs = int(data.get('num_logs', 100000))
        overlap = float(data.get('overlap_ratio', 0.20))
        bytes_per_row = 150

        matching_rows = int(n_logs * overlap)
        non_matching_rows = n_logs - matching_rows
        naive_cost_bytes = n_logs * bytes_per_row

        # Điểm tham chiếu: m tối ưu tại FPR=1%
        m_optimal = BloomFilter._optimal_size(n_subs, 0.01)

        # Quét giá trị m từ rất nhỏ (5% m_opt) đến khá lớn (300% m_opt)
        m_min = max(100, int(m_optimal * 0.05))
        m_max = int(m_optimal * 3.0)
        steps = 150

        m_values = []
        bf_costs_kb = []
        naive_costs_kb = []
        fpr_values_pct = []

        breakeven_m = None
        breakeven_cost_kb = None
        optimal_m = None
        optimal_cost_kb = None
        min_cost = float('inf')

        prev_bf_above_naive = True  # Trước điểm gãy, BF đắt hơn Naive

        for i in range(steps):
            m = int(m_min + (m_max - m_min) * i / (steps - 1))
            # Tính k tối ưu cho m này
            k = max(1, round((m / n_subs) * math.log(2)))

            # FPR theo công thức: (1 - e^(-kn/m))^k
            exponent = -k * n_subs / m
            fpr = (1 - math.exp(exponent)) ** k
            fpr = min(max(fpr, 0.0), 1.0)

            bf_size_bytes = math.ceil(m / 8)
            fp_rows = int(non_matching_rows * fpr)
            bf_total_bytes = bf_size_bytes + (matching_rows + fp_rows) * bytes_per_row

            bf_cost_kb = round(bf_total_bytes / 1024, 2)
            naive_cost_kb_val = round(naive_cost_bytes / 1024, 2)

            m_values.append(m)
            bf_costs_kb.append(bf_cost_kb)
            naive_costs_kb.append(naive_cost_kb_val)
            fpr_values_pct.append(round(fpr * 100, 4))

            # Tìm điểm gãy: lần đầu BF rẻ hơn Naive
            bf_above_naive = bf_total_bytes >= naive_cost_bytes
            if prev_bf_above_naive and not bf_above_naive and breakeven_m is None:
                breakeven_m = m
                breakeven_cost_kb = bf_cost_kb
            prev_bf_above_naive = bf_above_naive

            # Tìm điểm tối ưu (chi phí BF thấp nhất)
            if bf_total_bytes < min_cost:
                min_cost = bf_total_bytes
                optimal_m = m
                optimal_cost_kb = bf_cost_kb

        return jsonify({
            'success': True,
            'config': {
                'num_subscribers': n_subs,
                'num_logs': n_logs,
                'overlap_ratio': overlap,
                'naive_cost_kb': round(naive_cost_bytes / 1024, 2),
                'matching_rows': matching_rows,
                'non_matching_rows': non_matching_rows,
                'm_optimal_fpr1pct': m_optimal,
            },
            'm_values': m_values,
            'bf_costs_kb': bf_costs_kb,
            'naive_costs_kb': naive_costs_kb,
            'fpr_values_pct': fpr_values_pct,
            'breakeven': {
                'm_bits': breakeven_m,
                'm_kb': round(breakeven_m / 8 / 1024, 4) if breakeven_m else None,
                'cost_kb': breakeven_cost_kb,
                'saving_vs_naive_pct': round((naive_cost_bytes / 1024 - breakeven_cost_kb) / (naive_cost_bytes / 1024) * 100, 1) if breakeven_cost_kb else None,
            },
            'optimal': {
                'm_bits': optimal_m,
                'm_kb': round(optimal_m / 8 / 1024, 4) if optimal_m else None,
                'cost_kb': optimal_cost_kb,
                'saving_vs_naive_pct': round((naive_cost_bytes / 1024 - (optimal_cost_kb or 0)) / (naive_cost_bytes / 1024) * 100, 1),
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =================================================================
# API: MÔ PHỎNG PHÂN TÁN THẬT SỰ (2 processes qua HTTP)
# =================================================================

@app.route('/api/run-distributed', methods=['POST'])
def run_distributed():
    import requests as http_client
    
    SITE_B_URL = os.environ.get('SITE_B_URL', 'http://localhost:5001')
    
    try:
        data = request.get_json() or {}
        num_subs = min(int(data.get('num_subscribers', 10000)), 50000)
        num_logs = min(int(data.get('num_logs', 50000)), 200000)
        overlap  = float(data.get('overlap_ratio', 0.20))
        fpr_target = float(data.get('fpr_target', 0.01))
        
        timeline = []  # Ghi lại timeline để hiển thị trên frontend
        
        # ═══ BƯỚC 0: Kiểm tra Site B online ═══
        t0 = time.time()
        try:
            status_res = http_client.get(f'{SITE_B_URL}/api/status', timeout=3)
            status_data = status_res.json()
            if status_data.get('status') != 'online':
                return jsonify({'success': False, 'error': 'Node B is offline'}), 504
            timeline.append({
                'step': 0, 'label': 'Health check Site B',
                'detail': f'Site B online tại port 5001',
                'time_ms': round((time.time() - t0) * 1000, 1)
            })
        except http_client.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'error': 'Không thể kết nối đến Site B (port 5001). '
                         'Hãy chạy: python site_b_server.py'
            }), 504
        
        # ═══ BƯỚC 1: Tạo dữ liệu ═══
        t1 = time.time()
        generator = DataGenerator(seed=2024)
        subscribers, weblogs, analysis = generator.generate_scenario(
            scenario_name="Distributed Demo",
            num_subscribers=num_subs,
            num_logs=num_logs,
            overlap_ratio=overlap
        )
        timeline.append({
            'step': 1, 'label': 'Tạo dữ liệu',
            'detail': f'{num_subs:,} Subscribers + {num_logs:,} WebLogs',
            'time_ms': round((time.time() - t1) * 1000, 1)
        })
        
        # ═══ BƯỚC 2: Gửi WebLogs sang Site B qua HTTP ═══
        t2 = time.time()
        logs_payload = weblogs.to_dict(orient='records')
        logs_bytes_sent = len(json.dumps(logs_payload).encode('utf-8'))
        
        load_res = http_client.post(
            f'{SITE_B_URL}/api/load-data',
            json={'weblogs': logs_payload},
            timeout=30
        )
        load_data_resp = load_res.json()
        timeline.append({
            'step': 2, 'label': 'Gửi WebLogs → Site B (HTTP POST)',
            'detail': f'{num_logs:,} dòng ({logs_bytes_sent/1024:.1f} KB qua mạng)',
            'time_ms': round((time.time() - t2) * 1000, 1)
        })
        
        # ═══ BƯỚC 3: Site A tạo Bloom Filter ═══
        t3 = time.time()
        bf = BloomFilter(expected_items_n=num_subs, fp_rate=fpr_target)
        user_ids = subscribers['user_id'].tolist()
        bf.bulk_insert(user_ids)
        
        bf_bit_string = bf.bit_array.to01()  # Serialize thành chuỗi '010110...'
        bf_bytes = bf.get_size_bytes()
        
        timeline.append({
            'step': 3, 'label': 'Site A: Tạo Bloom Filter',
            'detail': f'm={bf.m:,} bits, k={bf.k}, size={bf_bytes:,} bytes',
            'time_ms': round((time.time() - t3) * 1000, 1)
        })
        
        # ═══ BƯỚC 4: Gửi BF sang Site B + Lọc ═══
        t4 = time.time()
        filter_res = http_client.post(
            f'{SITE_B_URL}/api/filter-logs',
            json={
                'bf_bit_string': bf_bit_string,
                'bf_m': bf.m,
                'bf_k': bf.k,
            },
            timeout=60
        )
        filter_data = filter_res.json()
        
        bf_payload_bytes = len(json.dumps({
            'bf_bit_string': bf_bit_string,
            'bf_m': bf.m,
            'bf_k': bf.k,
        }).encode('utf-8'))
        
        filter_stats = filter_data.get('stats', {})
        filtered_logs = filter_data.get('filtered_logs', [])
        
        timeline.append({
            'step': 4, 'label': 'Gửi BF → Site B + Lọc tại B + Nhận kết quả',
            'detail': f'Gửi BF ({bf_payload_bytes:,} bytes) → B lọc {filter_stats.get("total_rows", 0):,} dòng → '
                      f'trả {filter_stats.get("passed_rows", 0):,} dòng về A '
                      f'(loại {filter_stats.get("rejection_rate_pct", 0)}%)',
            'time_ms': round((time.time() - t4) * 1000, 1)
        })
        
        # ═══ BƯỚC 5: Site A — Inner Join cuối cùng ═══
        t5 = time.time()
        import pandas as pd
        filtered_df = pd.DataFrame(filtered_logs)
        
        if len(filtered_df) > 0:
            final_result = pd.merge(subscribers, filtered_df, on='user_id', how='inner')
        else:
            final_result = pd.DataFrame()
        
        # Đếm False Positives
        actual_set = set(user_ids)
        fp_count = 0
        if len(filtered_df) > 0:
            fp_count = len(filtered_df[~filtered_df['user_id'].isin(actual_set)])
        
        timeline.append({
            'step': 5, 'label': 'Site A: Inner Join cuối — loại FP',
            'detail': f'Join {len(filtered_df):,} filtered rows → {len(final_result):,} kết quả chính xác '
                      f'(loại {fp_count:,} False Positives)',
            'time_ms': round((time.time() - t5) * 1000, 1)
        })
        
        total_time = time.time() - t0
        
        # So sánh với Naive
        naive_bytes = num_logs * 150
        bf_total_network = bf_bytes + filter_stats.get('passed_rows', 0) * 150
        saving_pct = round((naive_bytes - bf_total_network) / naive_bytes * 100, 1)
        
        return jsonify({
            'success': True,
            'mode': 'distributed',
            'config': {
                'site_a_port': 5000,
                'site_b_port': 5001,
                'num_subscribers': num_subs,
                'num_logs': num_logs,
                'overlap_ratio': overlap,
                'fpr_target': fpr_target,
            },
            'timeline': timeline,
            'results': {
                'naive_cost_kb': round(naive_bytes / 1024, 2),
                'bf_cost_kb': round(bf_total_network / 1024, 2),
                'saving_pct': saving_pct,
                'bf_size_bytes': bf_bytes,
                'bf_m_bits': bf.m,
                'bf_k': bf.k,
                'rows_sent_to_b': num_logs,
                'rows_returned_from_b': filter_stats.get('passed_rows', 0),
                'rows_rejected_at_b': filter_stats.get('rejected_rows', 0),
                'false_positives': fp_count,
                'final_join_rows': len(final_result),
                'total_time_ms': round(total_time * 1000, 1),
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# =================================================================
# API: Sensitivity Analysis (Phân tích độ nhạy tham số)
# =================================================================

@app.route('/api/sensitivity-analysis', methods=['POST'])
def sensitivity_analysis():
    try:
        data = request.get_json() or {}
        n_subs = int(data.get('num_subscribers', 10000))
        n_logs = int(data.get('num_logs', 100000))
        fpr_target = float(data.get('fpr_target', 0.01))
        bytes_per_row = 150
        
        # Tham số BF cố định theo n_subs và fpr_target
        m = BloomFilter._optimal_size(n_subs, fpr_target)
        k = BloomFilter._optimal_hash_count(m, n_subs)
        bf_bytes = math.ceil(m / 8)
        
        # FPR lý thuyết
        fpr_actual = (1 - math.exp(-k * n_subs / m)) ** k
        
        overlaps = []
        naive_costs = []
        bf_costs = []
        savings_pct = []
        wasted_naive_pct = []  # Phần trăm dữ liệu thừa khi dùng Naive
        
        for ov_pct in range(5, 96, 5):
            ov = ov_pct / 100.0
            matching = int(n_logs * ov)
            non_matching = n_logs - matching
            
            naive_bytes_val = n_logs * bytes_per_row
            fp_rows = int(non_matching * fpr_actual)
            bf_total = bf_bytes + (matching + fp_rows) * bytes_per_row
            
            saving = max(0, round((naive_bytes_val - bf_total) / naive_bytes_val * 100, 2))
            
            overlaps.append(ov_pct)
            naive_costs.append(round(naive_bytes_val / 1024, 2))
            bf_costs.append(round(bf_total / 1024, 2))
            savings_pct.append(saving)
            wasted_naive_pct.append(round((1 - ov) * 100, 1))
        
        return jsonify({
            'success': True,
            'config': {
                'num_subscribers': n_subs,
                'num_logs': n_logs,
                'fpr_target': fpr_target,
                'fpr_actual': round(fpr_actual * 100, 4),
                'bf_m_bits': m,
                'bf_k': k,
                'bf_size_kb': round(bf_bytes / 1024, 4),
            },
            'overlaps': overlaps,
            'naive_costs_kb': naive_costs,
            'bf_costs_kb': bf_costs,
            'savings_pct': savings_pct,
            'wasted_naive_pct': wasted_naive_pct,
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =================================================================
# MAIN
# =================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  BLOOM FILTER JOIN OPTIMIZER - Web Dashboard")
    print("  Site A (Trung tâm) — http://localhost:5000")
    print("  [Ưu tiên 2] Chế độ phân tán: chạy thêm site_b_server.py")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)

