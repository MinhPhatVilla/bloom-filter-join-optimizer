"""
==========================================================================
FILE 4: VISUALIZATION - Trực Quan Hóa Kết Quả
==========================================================================
Môn: Cơ Sở Dữ Liệu Phân Tán
Đề tài: Bloom Filter Join Optimizer - "Subscribers & Logs"

File này vẽ các biểu đồ trực quan để minh họa:
  1. So sánh Bandwidth: Naive Join vs BF Semi-Join
  2. Tỷ lệ False Positive lý thuyết vs thực tế theo FPR
  3. Ảnh hưởng của Overlap Ratio đến hiệu quả tiết kiệm
  4. Kích thước Bloom Filter theo số phần tử và FPR
==========================================================================
"""

import math
import importlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# Import module BloomFilter từ file 1
bloom_mod = importlib.import_module("1_bloom_filter")
BloomFilter = bloom_mod.BloomFilter


# =================================================================
# CẤU HÌNH STYLE CHUNG (Dark Theme cho đẹp)
# =================================================================

def setup_style():
    """Cấu hình style chung cho tất cả biểu đồ."""
    plt.rcParams.update({
        'figure.facecolor': '#1e1e2e',
        'axes.facecolor': '#2a2a3e',
        'axes.edgecolor': '#444466',
        'axes.labelcolor': '#cdd6f4',
        'xtick.color': '#cdd6f4',
        'ytick.color': '#cdd6f4',
        'text.color': '#cdd6f4',
        'grid.color': '#444466',
        'grid.alpha': 0.5,
        'font.family': 'DejaVu Sans',
        'font.size': 10,
    })

COLORS = {
    'naive':   '#f38ba8',   # Đỏ hồng - Naive Join (xấu)
    'bf_10':   '#fab387',   # Cam      - BF FPR 10%
    'bf_5':    '#f9e2af',   # Vàng     - BF FPR 5%
    'bf_1':    '#a6e3a1',   # Xanh lá  - BF FPR 1%
    'bf_01':   '#89dceb',   # Xanh lam - BF FPR 0.1%
    'accent':  '#cba6f7',   # Tím      - Nhấn mạnh
    'match':   '#a6e3a1',   # Xanh lá  - Dữ liệu cần
    'waste':   '#f38ba8',   # Đỏ       - Lãng phí
}


# =================================================================
# BIỂU ĐỒ 1: So Sánh Bandwidth Các Chiến Lược
# =================================================================

def plot_bandwidth_comparison(benchmark_results, ax):
    """
    Vẽ biểu đồ cột so sánh lượng dữ liệu truyền qua mạng (KB).
    
    Parameters:
        benchmark_results: list kết quả từ DistributedJoinSimulator
        ax: Matplotlib Axes object
    """
    strategies = [r['strategy'] for r in benchmark_results]
    bandwidths  = [r['network_bytes'] / 1024 for r in benchmark_results]  # → KB
    
    bar_colors = [
        COLORS['naive'],
        COLORS['bf_10'],
        COLORS['bf_5'],
        COLORS['bf_1'],
        COLORS['bf_01'],
    ][:len(strategies)]

    bars = ax.bar(range(len(strategies)), bandwidths,
                  color=bar_colors, width=0.6, edgecolor='white', linewidth=0.5)

    # Label giá trị trên đầu mỗi cột
    for bar, val in zip(bars, bandwidths):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(bandwidths) * 0.01,
                f'{val:,.0f} KB', ha='center', va='bottom',
                fontsize=9, color='white', fontweight='bold')

    # % tiết kiệm so với Naive
    base = bandwidths[0]
    for i, (bar, val) in enumerate(zip(bars[1:], bandwidths[1:]), 1):
        savings = (base - val) / base * 100
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() / 2,
                f'-{savings:.0f}%', ha='center', va='center',
                fontsize=10, color='#1e1e2e', fontweight='bold')

    ax.set_xticks(range(len(strategies)))
    ax.set_xticklabels(strategies, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel('Băng thông mạng (KB)', fontsize=11)
    ax.set_title('So Sanh Bang Thong Mang: Naive Join vs BF Semi-Join',
                 fontsize=13, fontweight='bold', pad=12)
    ax.grid(axis='y', linestyle='--')
    ax.set_ylim(0, max(bandwidths) * 1.18)


# =================================================================
# BIỂU ĐỒ 2: FPR Lý Thuyết vs Thực Tế
# =================================================================

def plot_fpr_theory_vs_actual(benchmark_results, ax):
    """
    Vẽ biểu đồ đường so sánh FPR lý thuyết và False Positive thực đo được.
    
    Parameters:
        benchmark_results: list kết quả (bỏ qua Naive - index 0)
        ax: Matplotlib Axes object
    """
    # Lọc bỏ kết quả Naive Join
    bf_results = [r for r in benchmark_results if 'BF' in r['strategy']]

    fpr_targets   = [0.10, 0.05, 0.01, 0.001]
    fp_actual_pct = []

    total_logs = benchmark_results[0]['rows_transferred']   # Naive = gửi hết
    for r in bf_results:
        # FP thực tế tính theo % trên tổng dữ liệu đã lọc
        rows_sent = r['rows_transferred']
        fp        = r['false_positives']
        pct = fp / rows_sent * 100 if rows_sent > 0 else 0
        fp_actual_pct.append(pct)

    fpr_theory_pct = [f * 100 for f in fpr_targets]

    ax.plot(fpr_theory_pct, fpr_theory_pct, 'o--',
            color=COLORS['accent'], label='FPR Lý thuyết (setup)',
            linewidth=2, markersize=8)
    ax.plot(fpr_theory_pct, fp_actual_pct, 's-',
            color=COLORS['bf_1'], label='FP Thực tế (đo được)',
            linewidth=2, markersize=8)

    for x, y_th, y_ac in zip(fpr_theory_pct, fpr_theory_pct, fp_actual_pct):
        ax.annotate(f'{y_ac:.2f}%', (x, y_ac),
                    textcoords='offset points', xytext=(6, 4),
                    color='white', fontsize=8)

    ax.set_xlabel('FPR cài đặt (%)', fontsize=11)
    ax.set_ylabel('Tỷ lệ (%)', fontsize=11)
    ax.set_title('FPR Ly Thuyet vs Thuc Te', fontsize=13, fontweight='bold', pad=12)
    ax.legend(fontsize=9)
    ax.grid(linestyle='--')


# =================================================================
# BIỂU ĐỒ 3: Ảnh Hưởng của Overlap Ratio
# =================================================================

def plot_overlap_impact(ax):
    """
    Vẽ biểu đồ diện tích chồng chất: tỷ lệ match vs waste theo overlap.
    
    Parameters:
        ax: Matplotlib Axes object
    """
    overlap_ratios = np.linspace(0.05, 0.95, 50)
    match_pct = overlap_ratios * 100
    waste_pct = (1 - overlap_ratios) * 100

    ax.stackplot(overlap_ratios * 100, match_pct, waste_pct,
                 labels=['[+] Du lieu can thiet (match)', '[-] Du lieu lang phi (thua)'],
                 colors=[COLORS['match'], COLORS['waste']], alpha=0.85)

    # Vạch đứng ở overlap = 35% (kịch bản tiêu chuẩn)
    ax.axvline(x=35, color='white', linestyle=':', linewidth=1.5)
    ax.text(37, 50, 'Kịch bản\ntiêu chuẩn\n(35%)', color='white', fontsize=8)

    ax.set_xlabel('Overlap Ratio (%)', fontsize=11)
    ax.set_ylabel('Tỷ lệ dữ liệu (%)', fontsize=11)
    ax.set_title('Anh Huong Overlap Ratio den Lang Phi Bang Thong',
                 fontsize=13, fontweight='bold', pad=12)
    ax.legend(loc='center right', fontsize=9)
    ax.set_xlim(5, 95)
    ax.set_ylim(0, 100)
    ax.grid(linestyle='--')


# =================================================================
# BIỂU ĐỒ 4: Kích Thước Bloom Filter theo n và FPR
# =================================================================

def plot_bf_size(ax):
    """
    Vẽ biểu đồ kích thước BF (MB) theo số phần tử n với nhiều mức FPR.
    
    Parameters:
        ax: Matplotlib Axes object
    """
    n_values = np.linspace(1000, 1_000_000, 200)
    fpr_list = [0.10, 0.05, 0.01, 0.001]
    line_colors = [COLORS['bf_10'], COLORS['bf_5'], COLORS['bf_1'], COLORS['bf_01']]
    labels = ['FPR 10%', 'FPR 5%', 'FPR 1%', 'FPR 0.1%']

    for fpr, color, label in zip(fpr_list, line_colors, labels):
        sizes_mb = []
        for n in n_values:
            m = BloomFilter._optimal_size(int(n), fpr)
            sizes_mb.append(m / 8 / 1024 / 1024)
        ax.plot(n_values / 1000, sizes_mb, color=color, label=label, linewidth=2)

    ax.set_xlabel('Số phần tử (nghìn)', fontsize=11)
    ax.set_ylabel('Kích thước Bloom Filter (MB)', fontsize=11)
    ax.set_title('Kich Thuoc BF theo So Phan Tu & FPR',
                 fontsize=13, fontweight='bold', pad=12)
    ax.legend(fontsize=9)
    ax.grid(linestyle='--')


# =================================================================
# HÀM CHÍNH: Vẽ Dashboard Tổng Hợp
# =================================================================

def draw_full_dashboard(benchmark_results):
    """
    Vẽ toàn bộ dashboard 2x2 gồm 4 biểu đồ và lưu ảnh.
    
    Parameters:
        benchmark_results: list kết quả từ DistributedJoinSimulator.compare_strategies()
    """
    setup_style()

    fig = plt.figure(figsize=(18, 11))
    fig.suptitle(
        'Bloom Filter Semi-Join Optimizer — Dashboard Phan Tich',
        fontsize=16, fontweight='bold', color='white', y=0.98
    )

    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    plot_bandwidth_comparison(benchmark_results, ax1)
    plot_fpr_theory_vs_actual(benchmark_results, ax2)
    plot_overlap_impact(ax3)
    plot_bf_size(ax4)

    output_path = 'dashboard.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f'\n  ✅ Dashboard đã lưu tại: {output_path}')
    plt.show()


# =================================================================
# DEMO NHANH (chạy độc lập không cần File 3)
# =================================================================

if __name__ == '__main__':
    print('=' * 65)
    print('  DEMO: Visualization - Trực Quan Hóa Kết Quả')
    print('=' * 65)

    # Tạo benchmark_results giả để test nhanh (không cần chạy simulation)
    TOTAL_LOGS = 50_000
    BYTES_PER_ROW = 150
    naive_bytes = TOTAL_LOGS * BYTES_PER_ROW

    # Giả lập kết quả từ File 3 (DistributedJoinSimulator)
    fake_results = [
        {'strategy': 'Naive Join',          'network_bytes': naive_bytes,
         'rows_transferred': 50000, 'false_positives': 0},
        {'strategy': 'BF Semi-Join (10%)',  'network_bytes': int(naive_bytes * 0.28),
         'rows_transferred': 14000, 'false_positives': 4000},
        {'strategy': 'BF Semi-Join (5%)',   'network_bytes': int(naive_bytes * 0.24),
         'rows_transferred': 11900, 'false_positives': 1900},
        {'strategy': 'BF Semi-Join (1%)',   'network_bytes': int(naive_bytes * 0.21),
         'rows_transferred': 10400, 'false_positives': 400},
        {'strategy': 'BF Semi-Join (0.1%)', 'network_bytes': int(naive_bytes * 0.20),
         'rows_transferred': 10050, 'false_positives': 50},
    ]

    draw_full_dashboard(fake_results)
