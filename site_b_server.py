"""
==========================================================================
SITE B SERVER — Flask Server Giả Lập Node B (Web Server Site)
==========================================================================
Chạy ĐỘC LẬP trên port 5001.

Đây là bằng chứng hệ thống phân tán THẬT SỰ:
  - Site A (port 5000): Trung tâm — giữ bảng Subscribers
  - Site B (port 5001): Chi nhánh — giữ bảng WebLogs

Giao tiếp giữa Site A ↔ Site B hoàn toàn qua HTTP REST API.

Cách chạy:
    Terminal 1: python site_b_server.py      (Site B — port 5001)
    Terminal 2: python app.py                (Site A — port 5000)
==========================================================================
"""

import sys
import io
import json
import time
import importlib
import warnings
warnings.filterwarnings('ignore')

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

# Import Bloom Filter module (chỉ dùng class, KHÔNG dùng thư viện BF có sẵn)
bloom_mod = importlib.import_module("1_bloom_filter")
BloomFilter = bloom_mod.BloomFilter

app = Flask(__name__)
CORS(app)  # Cho phép Site A (port 5000) gọi sang Site B (port 5001)

# =================================================================
# STATE: Dữ liệu WebLogs được giữ tại Site B (bộ nhớ)
# =================================================================
site_b_data = {
    'weblogs_df': None,       # DataFrame WebLogs — dữ liệu cục bộ của Site B
    'status': 'online',       # Trạng thái: 'online' | 'offline'
    'request_count': 0,       # Đếm số lần xử lý request (thống kê)
    'total_rows_filtered': 0, # Tổng số dòng đã lọc qua tất cả request
}


# =================================================================
# HEALTH CHECK — Kiểm tra Site B đang hoạt động
# =================================================================

@app.route('/api/status')
def get_status():
    """Trả về trạng thái sức khoẻ của Site B."""
    return jsonify({
        'status': site_b_data['status'],
        'site': 'Site B (Web Server)',
        'port': 5001,
        'has_data': site_b_data['weblogs_df'] is not None,
        'data_rows': len(site_b_data['weblogs_df']) if site_b_data['weblogs_df'] is not None else 0,
        'request_count': site_b_data['request_count'],
        'total_rows_filtered': site_b_data['total_rows_filtered'],
    })


# =================================================================
# LOAD DATA — Site A gửi dữ liệu WebLogs cho Site B giữ
# =================================================================

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """
    Nhận dữ liệu WebLogs từ Site A và lưu tại bộ nhớ Site B.
    
    Body (JSON):
        weblogs: list of dicts (mỗi dict = 1 dòng WebLog)
    """
    try:
        data = request.get_json()
        records = data.get('weblogs', [])
        
        site_b_data['weblogs_df'] = pd.DataFrame(records)
        num_rows = len(site_b_data['weblogs_df'])
        
        print(f"[Site B] ✅ Đã nhận {num_rows:,} dòng WebLogs từ Site A")
        
        return jsonify({
            'success': True,
            'rows_loaded': num_rows,
            'columns': list(site_b_data['weblogs_df'].columns),
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =================================================================
# FILTER LOGS — Lọc WebLogs bằng Bloom Filter nhận từ Site A
# =================================================================

@app.route('/api/filter-logs', methods=['POST'])
def filter_logs():
    """
    Bước cốt lõi của BF Semi-Join tại Site B.
    
    Nhận Bloom Filter (dạng bit string) từ Site A,
    dùng nó để lọc bảng WebLogs cục bộ,
    chỉ trả về những dòng PASS qua Bloom Filter.
    
    Body (JSON):
        bf_bit_string: str (chuỗi '0'/'1' đại diện bit_array)
        bf_m: int (kích thước bit array)
        bf_k: int (số hàm băm)
        
    Returns:
        filtered_logs: list of dicts
        stats: thống kê lọc
    """
    try:
        if site_b_data['weblogs_df'] is None:
            return jsonify({'success': False, 'error': 'Site B chưa có dữ liệu WebLogs'}), 400
        
        data = request.get_json()
        bf_bit_string = data['bf_bit_string']
        bf_m = int(data['bf_m'])
        bf_k = int(data['bf_k'])
        
        t_start = time.time()
        
        # ───────────────────────────────────────────────
        # RECONSTRUCT Bloom Filter từ bit string nhận được
        # ───────────────────────────────────────────────
        # (Đây chính xác là điều xảy ra trong hệ thống phân tán thật:
        #  Site A serialize BF → truyền qua mạng → Site B deserialize)
        bf = BloomFilter(size_m=bf_m, num_hashes_k=bf_k)
        
        from bitarray import bitarray as ba
        received_bits = ba(bf_bit_string)
        bf.bit_array = received_bits
        
        bf_size_bytes = len(bf_bit_string) // 8  # Kích thước BF nhận qua mạng
        
        # ───────────────────────────────────────────────
        # LỌC WebLogs qua Bloom Filter tại Site B
        # ───────────────────────────────────────────────
        logs_df = site_b_data['weblogs_df']
        total_rows = len(logs_df)
        
        mask = logs_df['user_id'].apply(lambda uid: bf.lookup(uid))
        filtered_df = logs_df[mask]
        
        passed_rows = len(filtered_df)
        rejected_rows = total_rows - passed_rows
        
        t_elapsed = time.time() - t_start
        
        # Cập nhật thống kê Site B
        site_b_data['request_count'] += 1
        site_b_data['total_rows_filtered'] += total_rows
        
        print(f"[Site B] 🔍 Lọc BF: {total_rows:,} → {passed_rows:,} dòng "
              f"(loại bỏ {rejected_rows:,} = {rejected_rows/total_rows*100:.1f}%) "
              f"[{t_elapsed*1000:.0f}ms]")
        
        # Trả filtered logs về Site A dưới dạng JSON
        return jsonify({
            'success': True,
            'filtered_logs': filtered_df.to_dict(orient='records'),
            'stats': {
                'total_rows': total_rows,
                'passed_rows': passed_rows,
                'rejected_rows': rejected_rows,
                'rejection_rate_pct': round(rejected_rows / total_rows * 100, 2),
                'bf_m_bits': bf_m,
                'bf_k_hashes': bf_k,
                'bf_received_bytes': bf_size_bytes,
                'filter_time_ms': round(t_elapsed * 1000, 1),
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# =================================================================
# KILL — Mô phỏng sập Node B (cho demo)
# =================================================================

@app.route('/api/kill', methods=['POST'])
def kill_node():
    """Mô phỏng Node B bị sập."""
    site_b_data['status'] = 'offline'
    print("[Site B] ❌ Node B đã bị KILL — mô phỏng sập server")
    return jsonify({'status': 'offline', 'message': 'Node B is now offline'})


@app.route('/api/recover', methods=['POST'])
def recover_node():
    """Mô phỏng Node B khôi phục."""
    site_b_data['status'] = 'online'
    print("[Site B] ✅ Node B đã KHÔI PHỤC — sẵn sàng hoạt động")
    return jsonify({'status': 'online', 'message': 'Node B is back online'})


# =================================================================
# MAIN
# =================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  SITE B SERVER — Node B (Web Server Site)")
    print("  Listening on: http://localhost:5001")
    print("  Waiting for data from Site A (port 5000)...")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5001, use_reloader=False)
