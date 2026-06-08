/* ==========================================================
   BLOOM FILTER JOIN OPTIMIZER — Frontend Logic v2.0
   Smooth animations · Count-up · Pipeline flow · ScrollSpy
   ========================================================== */

// ─── Chart instances (global) ───
let chartBandwidth = null;
let chartFpr = null;
let chartOverlap = null;
let chartBfSize = null;

// ─── Loading step animation handle ───
let loadingTimers = [];

// ─── Color palette (Catppuccin-inspired) ───
const COLORS = {
  naive:    '#ff6b9d',
  bf10:     '#ff8c42',
  bf5:      '#ffd166',
  bf1:      '#00e887',
  bf01:     '#00d4ff',
  purple:   '#b87fff',
  teal:     '#4ecdc4',
  text:     '#e2e8f4',
  muted:    '#5a6080',
  grid:     'rgba(255,255,255,0.05)',
};
const CHART_COLORS = [COLORS.naive, COLORS.bf10, COLORS.bf5, COLORS.bf1, COLORS.bf01];

// Chart.js global defaults
Chart.defaults.color = COLORS.text;
Chart.defaults.borderColor = COLORS.grid;
Chart.defaults.font.family = "'Inter', sans-serif";

// ==========================================================
// INIT ON DOM READY
// ==========================================================
document.addEventListener('DOMContentLoaded', () => {
  createParticles();
  initScrollReveal();
  initNavbarScroll();
  initSliders();
  initNodeBSwitch();
  initOverlapChart();
  initBfSizeChart();
  // Khởi tạo tab navigation
  switchTab('hero');
});

function initNodeBSwitch() {
  const switchNodeB = document.getElementById('switch-node-b');
  const lblNodeBStatus = document.getElementById('lbl-node-b-status');
  if (!switchNodeB || !lblNodeBStatus) return;

  switchNodeB.addEventListener('change', () => {
    if (switchNodeB.checked) {
      lblNodeBStatus.textContent = "ONLINE (Hoạt động)";
      lblNodeBStatus.classList.remove('text-pink');
      lblNodeBStatus.classList.add('text-green');
    } else {
      lblNodeBStatus.textContent = "OFFLINE (Đã tắt)";
      lblNodeBStatus.classList.remove('text-green');
      lblNodeBStatus.classList.add('text-pink');
    }
  });
}

// ==========================================================
// PARTICLES — data flow animation
// ==========================================================
function createParticles() {
  const container = document.getElementById('hero-particles');
  if (!container) return;
  const palette = [
    'rgba(184,127,255,VAL)', // purple
    'rgba(0,212,255,VAL)',   // cyan
    'rgba(0,232,135,VAL)',   // green
    'rgba(255,255,255,VAL)', // white
  ];
  for (let i = 0; i < 55; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size   = 1.5 + Math.random() * 3;
    const dur    = 10 + Math.random() * 18;
    const opacity = 0.15 + Math.random() * 0.45;
    const color  = palette[Math.floor(Math.random() * palette.length)].replace('VAL', opacity.toFixed(2));
    const tx     = (Math.random() - 0.2) * 160;  // mostly drift right
    const ty     = -(60 + Math.random() * 180);  // float upward
    p.style.cssText = `
      left:   ${Math.random() * 100}%;
      top:    ${20 + Math.random() * 70}%;
      width:  ${size}px;
      height: ${size}px;
      background: ${color};
      --dur: ${dur}s;
      --op:  ${opacity};
      --tx:  ${tx}px;
      --ty:  ${ty}px;
      animation-delay: ${Math.random() * dur}s;
    `;
    container.appendChild(p);
  }
}

// ==========================================================
// SCROLL REVEAL (IntersectionObserver)
// ==========================================================
function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay || '0');
        setTimeout(() => entry.target.classList.add('visible'), delay);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
}

// ==========================================================
// TAB NAVIGATION
// ==========================================================
function switchTab(tabId) {
  // Ẩn tất cả các tab-page
  document.querySelectorAll('.tab-page').forEach(page => {
    page.classList.remove('active');
  });

  // Hiện tab được chọn
  const target = document.querySelector(`.tab-page[data-tab-id="${tabId}"]`);
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Cập nhật nav-link active
  document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
    link.classList.toggle('active', link.dataset.tab === tabId);
  });

  // Đóng mobile menu nếu đang mở
  const navLinks = document.getElementById('nav-links');
  const hamburger = document.getElementById('nav-hamburger');
  if (navLinks) navLinks.classList.remove('mobile-open');
  if (hamburger) hamburger.classList.remove('open');
}

// ==========================================================
// SCROLLSPY — đã tắt (không dùng khi dùng tab navigation)
// ==========================================================
function initScrollSpy() {
  // Disabled — replaced by tab navigation
}

// ==========================================================
// NAVBAR SCROLL EFFECT
// ==========================================================
function initNavbarScroll() {
  const navbar = document.getElementById('navbar');
  const onScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
}

// ==========================================================
// MOBILE MENU TOGGLE
// ==========================================================
function toggleMobileMenu() {
  const navLinks   = document.getElementById('nav-links');
  const hamburger  = document.getElementById('nav-hamburger');
  const isOpen     = navLinks.classList.toggle('mobile-open');
  hamburger.classList.toggle('open', isOpen);
  // Đóng menu khi click vào link
  if (isOpen) {
    navLinks.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('mobile-open');
        hamburger.classList.remove('open');
      }, { once: true });
    });
  }
}

// ==========================================================
// SLIDERS
// ==========================================================
function updateSliderFill(slider) {
  const min  = parseFloat(slider.min)  || 0;
  const max  = parseFloat(slider.max)  || 100;
  const val  = parseFloat(slider.value);
  const pct  = ((val - min) / (max - min) * 100).toFixed(1) + '%';
  slider.style.setProperty('--fill', pct);
}

function initSliders() {
  const sliderSubs    = document.getElementById('slider-subs');
  const sliderLogs    = document.getElementById('slider-logs');
  const sliderOverlap = document.getElementById('slider-overlap');

  // Init fill on load
  updateSliderFill(sliderSubs);
  updateSliderFill(sliderLogs);
  updateSliderFill(sliderOverlap);

  sliderSubs.addEventListener('input', () => {
    document.getElementById('val-subs').textContent = Number(sliderSubs.value).toLocaleString();
    updateSliderFill(sliderSubs);
  });
  sliderLogs.addEventListener('input', () => {
    document.getElementById('val-logs').textContent = Number(sliderLogs.value).toLocaleString();
    updateSliderFill(sliderLogs);
  });
  sliderOverlap.addEventListener('input', () => {
    const v = sliderOverlap.value;
    document.getElementById('val-overlap').textContent = v;
    updateSliderFill(sliderOverlap);
    const hint = document.getElementById('overlap-hint');
    if (hint) hint.textContent = `~${100 - v}% guest logs (không phải subscriber)`;
  });
}

// ==========================================================
// COUNT-UP ANIMATION
// ==========================================================
function countUp(el, targetStr, duration = 1400) {
  // Parse number + suffix (e.g. "79.8%", "30.4s", "50,000")
  const cleaned = targetStr.replace(/,/g, '');
  const num = parseFloat(cleaned);
  if (isNaN(num)) { el.textContent = targetStr; return; }
  const suffix = targetStr.replace(/[\d.,]/g, '');
  const decimals = (cleaned.split('.')[1] || '').length;

  const startTime = performance.now();
  const step = (now) => {
    const t = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
    const val = num * eased;
    const formatted = val.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    el.textContent = formatted + suffix;
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = targetStr; // snap to exact value
  };
  requestAnimationFrame(step);
}

// ==========================================================
// PIPELINE ANIMATION
// ==========================================================
function animatePipeline(results) {
  const steps      = document.querySelectorAll('.pipeline-step');
  const connectors = document.querySelectorAll('.pipeline-connector');

  // Reset
  steps.forEach(s => s.classList.remove('active', 'done'));
  connectors.forEach(c => c.classList.remove('active'));

  // Attach size badges if results available
  if (results) {
    const best = results.filter(r => r.bf_size_kb)[0];
    if (best) {
      const b1 = document.getElementById('step-badge-1');
      const b2 = document.getElementById('step-badge-2');
      const b3 = document.getElementById('step-badge-3');
      const b4 = document.getElementById('step-badge-4');
      const b5 = document.getElementById('step-badge-5');
      if (b1) b1.textContent = `${fmtNum(results[0].rows_transferred)} logs`;
      if (b2) b2.textContent = `~${best.bf_size_kb} KB`;
      if (b3) b3.textContent = `Lọc ~${Math.round((1 - results[0].final_rows / results[0].rows_transferred) * 100 + (results.find(r=>r.saving_pct > 0)?.saving_pct||79))}%`;
      if (b4) b4.textContent = `~${fmtNum(results.find(r => r.bf_size_kb)?.rows_transferred || 0)} logs`;
      if (b5) b5.textContent = `${fmtNum(results[0].final_rows)} rows ✓`;
    }
  }

  const STEP_INTERVAL = 800;
  // Sequence: step1 → conn1 → step2 → conn2 → ... → step5
  steps.forEach((step, i) => {
    const delay = i * STEP_INTERVAL * 2;
    setTimeout(() => {
      // Mark previous as done
      if (i > 0) {
        steps[i - 1].classList.remove('active');
        steps[i - 1].classList.add('done');
      }
      step.classList.add('active');
    }, delay);

    // Animate connector after step activates
    if (connectors[i]) {
      setTimeout(() => {
        connectors[i].classList.add('active');
      }, delay + STEP_INTERVAL);
    }
  });

  // Mark last step done
  setTimeout(() => {
    steps[steps.length - 1].classList.remove('active');
    steps[steps.length - 1].classList.add('done');
  }, steps.length * STEP_INTERVAL * 2);
}

// ==========================================================
// LOADING SCREEN — MULTI-STEP
// ==========================================================
function startLoadingAnimation(estimatedMs = 12000) {
  const totalSteps = 5;
  const stepMs = estimatedMs / totalSteps;
  loadingTimers = [];

  // Reset all steps
  for (let i = 0; i < totalSteps; i++) {
    const item = document.getElementById(`ls-${i}`);
    if (item) {
      item.classList.remove('active', 'done');
    }
  }
  document.getElementById('loading-bar-fill').style.width = '0%';

  // Activate steps one by one
  for (let i = 0; i < totalSteps; i++) {
    loadingTimers[i] = setTimeout(() => {
      // Mark previous done
      if (i > 0) {
        const prev = document.getElementById(`ls-${i - 1}`);
        if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
      }
      const curr = document.getElementById(`ls-${i}`);
      if (curr) { curr.classList.add('active'); }
      // Update progress bar
      document.getElementById('loading-bar-fill').style.width = `${((i + 1) / totalSteps) * 80}%`;
    }, i * stepMs);
  }
}

function finishLoadingAnimation() {
  // Cancel pending timers
  loadingTimers.forEach(t => clearTimeout(t));

  // Mark all done
  for (let i = 0; i < 5; i++) {
    const item = document.getElementById(`ls-${i}`);
    if (item) {
      item.classList.remove('active');
      item.classList.add('done');
    }
  }
  document.getElementById('loading-bar-fill').style.width = '100%';
}

function resetPipelineError() {
  const steps = document.querySelectorAll('.pipeline-step');
  const connectors = document.querySelectorAll('.pipeline-connector');
  steps.forEach(s => s.classList.remove('error'));
  connectors.forEach(c => c.classList.remove('error'));
}

function handlePipelineConnectionError() {
  const steps = document.querySelectorAll('.pipeline-step');
  const connectors = document.querySelectorAll('.pipeline-connector');
  
  // reset all statuses
  steps.forEach(s => s.classList.remove('active', 'done'));
  connectors.forEach(c => c.classList.remove('active'));
  
  // Bước 1: Site A vẫn tạo được Bloom Filter
  steps[0].classList.add('done');
  const b1 = document.getElementById('step-badge-1');
  if (b1) b1.textContent = "Khởi tạo BF thành công";

  // Trì hoãn một chút để tạo cảm giác truyền tin qua mạng
  setTimeout(() => {
    // Connector 1: A -> B bị đứt
    connectors[0].classList.add('error');
    steps[1].classList.add('error'); // Bước 2 lỗi
    const b2 = document.getElementById('step-badge-2');
    if (b2) b2.textContent = "MẤT KẾT NỐI ✖";
  }, 600);

  // Các bước tiếp theo (3, 4, 5) đều bị lỗi đỏ vì không thể tiếp tục giao dịch phân tán
  setTimeout(() => {
    for (let i = 2; i < steps.length; i++) {
      steps[i].classList.add('error');
      const badge = document.getElementById(`step-badge-${i + 1}`);
      if (badge) badge.textContent = "ABORTED ✖";
    }
    for (let i = 1; i < connectors.length; i++) {
      connectors[i].classList.add('error');
    }
    // Tự động hiện Recovery Banner sau khi lỗi được vẽ xong
    showRecoveryBanner();
  }, 1200);
}

// ==========================================================
// NODE B RECOVERY
// ==========================================================

/** Hiện Recovery Banner sau khi Node B bị kill */
function showRecoveryBanner() {
  const banner = document.getElementById('recovery-banner');
  if (banner) banner.style.display = 'block';
}

/** Khôi phục Node B và reset pipeline về trạng thái sẵn sàng */
function recoverNodeB() {
  // 1. Ẩn banner
  const banner = document.getElementById('recovery-banner');
  if (banner) banner.style.display = 'none';

  // 2. Bật lại switch Node B (ONLINE)
  const switchNodeB = document.getElementById('switch-node-b');
  const lblStatus = document.getElementById('lbl-node-b-status');
  if (switchNodeB) {
    switchNodeB.checked = true;
    if (lblStatus) {
      lblStatus.textContent = "ONLINE (Hoạt động)";
      lblStatus.classList.remove('text-pink');
      lblStatus.classList.add('text-green');
    }
  }

  // 3. Reset pipeline về trạng thái mặc định (không lỗi, không done)
  const steps = document.querySelectorAll('.pipeline-step');
  const connectors = document.querySelectorAll('.pipeline-connector');
  steps.forEach(s => {
    s.classList.remove('active', 'done', 'error');
    // Xóa text badge
    const badge = s.querySelector('.step-badge');
    if (badge) badge.textContent = '';
  });
  connectors.forEach(c => c.classList.remove('active', 'error'));

  // 4. Hiện thông báo recovery thành công bằng flash animation nhẹ
  steps.forEach((s, i) => {
    setTimeout(() => {
      s.style.transition = 'box-shadow 0.4s ease';
      s.querySelector('.step-card').style.boxShadow = '0 0 20px rgba(0, 232, 135, 0.4)';
      setTimeout(() => {
        s.querySelector('.step-card').style.boxShadow = '';
      }, 700);
    }, i * 120);
  });

  // 5. Kích hoạt lại nút Chạy Mô Phỏng
  document.getElementById('btn-simulate')?.removeAttribute('disabled');
  document.getElementById('btn-run-demo')?.removeAttribute('disabled');

  // 6. Hiện toast thông báo
  showToast('✅ Node B đã khôi phục kết nối! Sẵn sàng chạy lại giao dịch phân tán.');
}

/** Hiện toast notification nhỏ ở góc phải */
function showToast(message, type = 'success') {
  const existing = document.getElementById('app-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'app-toast';
  toast.style.cssText = `
    position: fixed; bottom: 28px; right: 28px; z-index: 9999;
    background: ${type === 'success' ? 'rgba(0, 232, 135, 0.12)' : 'rgba(248, 113, 113, 0.12)'};
    border: 1px solid ${type === 'success' ? 'rgba(0, 232, 135, 0.4)' : 'rgba(248, 113, 113, 0.4)'};
    color: ${type === 'success' ? '#00e887' : '#f87171'};
    padding: 14px 22px; border-radius: 12px;
    font-size: 0.88rem; font-family: 'Inter', sans-serif; font-weight: 500;
    backdrop-filter: blur(16px); max-width: 380px;
    animation: slideUp 0.4s cubic-bezier(0.22, 1, 0.36, 1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  `;
  toast.textContent = message;

  const style = document.createElement('style');
  style.textContent = '@keyframes slideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }';
  document.head.appendChild(style);
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ==========================================================
// BREAKEVEN ANALYSIS
// ==========================================================

let chartBreakeven = null;

async function runBreakevenAnalysis() {
  const nSubs   = parseInt(document.getElementById('be-subs').value) || 10000;
  const nLogs   = parseInt(document.getElementById('be-logs').value) || 100000;
  const overlap = (parseInt(document.getElementById('be-overlap').value) || 20) / 100;

  const btn = document.getElementById('btn-breakeven');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Đang tính...'; }

  try {
    const res  = await fetch('/api/breakeven-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_subscribers: nSubs, num_logs: nLogs, overlap_ratio: overlap })
    });
    const data = await res.json();

    if (!data.success) {
      alert('Lỗi: ' + data.error);
      return;
    }

    // Cập nhật info cards
    document.getElementById('be-naive-cost').textContent  = fmtNum(Math.round(data.config.naive_cost_kb)) + ' KB';
    
    const beM = data.breakeven;
    if (beM.m_bits) {
      document.getElementById('be-breakeven-m').textContent = fmtNum(beM.m_bits) + ' bits';
      document.getElementById('be-breakeven-sub').textContent = `≈ ${beM.m_kb} KB — BF bắt đầu rẻ hơn Naive`;
    } else {
      document.getElementById('be-breakeven-m').textContent = 'Không có';
      document.getElementById('be-breakeven-sub').textContent = 'BF Semi-Join luôn có lợi với dữ liệu này';
    }

    const optM = data.optimal;
    document.getElementById('be-optimal-m').textContent = fmtNum(optM.m_bits) + ' bits';
    document.getElementById('be-optimal-sub').textContent = `Chi phí tối thiểu: ${fmtNum(Math.round(optM.cost_kb))} KB`;
    document.getElementById('be-max-saving').textContent  = optM.saving_vs_naive_pct + '%';

    // Vẽ chart
    renderBreakevenChart(data);

    // Hiện interpretation box
    buildBreakevenInterpretation(data);

    // Hiện chart, ẩn placeholder
    document.getElementById('be-chart-placeholder').style.display = 'none';
    document.getElementById('be-chart-wrap').style.display = 'block';

  } catch (err) {
    alert('Không thể kết nối server.');
    console.error(err);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<span class="btn-shine"></span>🔍 Phân Tích'; }
  }
}

function renderBreakevenChart(data) {
  if (chartBreakeven) chartBreakeven.destroy();
  const ctx = document.getElementById('chart-breakeven').getContext('2d');

  // Chuẩn bị dữ liệu: chỉ lấy mỗi 2 điểm để chart không quá dày
  const step = Math.max(1, Math.floor(data.m_values.length / 80));
  const labels = data.m_values.filter((_, i) => i % step === 0).map(m => (m / 1000).toFixed(1) + 'K');
  const bfCosts = data.bf_costs_kb.filter((_, i) => i % step === 0);
  const naiveCosts = data.naive_costs_kb.filter((_, i) => i % step === 0);

  // Tìm index break-even trong filtered data
  const mValues_filtered = data.m_values.filter((_, i) => i % step === 0);
  const beM = data.breakeven.m_bits;
  let beIdx = -1;
  if (beM) {
    for (let i = 0; i < mValues_filtered.length; i++) {
      if (mValues_filtered[i] >= beM) { beIdx = i; break; }
    }
  }

  // Màu điểm: đỏ trước breakeven, xanh sau breakeven
  const bfPointColors = bfCosts.map((_, i) => {
    if (beIdx < 0) return 'rgba(0, 232, 135, 0.6)';
    return i < beIdx ? 'rgba(248, 113, 113, 0.6)' : 'rgba(0, 232, 135, 0.6)';
  });

  chartBreakeven = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Naive Join (Gửi toàn bộ)',
          data: naiveCosts,
          borderColor: '#f87171',
          borderWidth: 2,
          borderDash: [8, 4],
          pointRadius: 0,
          fill: false,
          tension: 0,
        },
        {
          label: 'BF Semi-Join (Chi phí thực)',
          data: bfCosts,
          borderColor: '#818cf8',
          borderWidth: 2.5,
          pointRadius: bfCosts.map((_, i) => (i === beIdx ? 7 : 0)),
          pointBackgroundColor: bfCosts.map((_, i) => (i === beIdx ? '#facc15' : '#818cf8')),
          pointBorderColor: '#facc15',
          fill: {
            target: 0,
            above: 'rgba(248, 113, 113, 0.05)',
            below: 'rgba(0, 232, 135, 0.07)',
          },
          tension: 0.3,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: { color: '#9aa3bc', font: { size: 12 }, boxWidth: 24, padding: 16 }
        },
        tooltip: {
          backgroundColor: 'rgba(16,16,30,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#e2e8f4',
          bodyColor: '#9aa3bc',
          padding: 12,
          callbacks: {
            title: (items) => `m = ${items[0].label} bits`,
            label: (item) => ` ${item.dataset.label}: ${fmtNum(Math.round(item.raw))} KB`
          }
        },
        annotation: beIdx >= 0 ? {
          annotations: {
            breakEvenLine: {
              type: 'line',
              xMin: beIdx,
              xMax: beIdx,
              borderColor: '#facc15',
              borderWidth: 2,
              borderDash: [5, 3],
              label: {
                display: true,
                content: '⚡ Break-even',
                color: '#facc15',
                backgroundColor: 'rgba(250, 204, 21, 0.1)',
                position: 'start',
                font: { size: 11, weight: '600' }
              }
            }
          }
        } : {}
      },
      scales: {
        x: {
          title: { display: true, text: 'Kích thước Bloom Filter (m, đơn vị: nghìn bits)', color: '#5a6080', font: { size: 11 } },
          ticks: { color: '#5a6080', maxTicksLimit: 12, font: { size: 10 } },
          grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
          title: { display: true, text: 'Chi phí băng thông mạng (KB)', color: '#5a6080', font: { size: 11 } },
          ticks: {
            color: '#5a6080',
            font: { size: 10 },
            callback: (v) => fmtNum(Math.round(v)) + ' KB'
          },
          grid: { color: 'rgba(255,255,255,0.04)' }
        }
      }
    }
  });
}

function buildBreakevenInterpretation(data) {
  const box = document.getElementById('be-interpretation');
  const text = document.getElementById('be-interpretation-text');
  if (!box || !text) return;

  const naive = fmtNum(Math.round(data.config.naive_cost_kb));
  const opt   = fmtNum(Math.round(data.optimal.cost_kb));
  const savedPct = data.optimal.saving_vs_naive_pct;
  const beMBits = data.breakeven.m_bits ? fmtNum(data.breakeven.m_bits) : null;
  const beKB    = data.breakeven.m_kb;

  let html = `
    <strong>Phân tích Break-even Point</strong><br>
    Với ${fmtNum(data.config.num_subscribers)} Subscribers và ${fmtNum(data.config.num_logs)} WebLogs 
    (Overlap = ${Math.round(data.config.overlap_ratio * 100)}%):<br><br>
    
    • <span class="highlight-red">Naive Join</span>: Tốn <strong>${naive} KB</strong> — gửi toàn bộ ${fmtNum(data.config.num_logs)} dòng log qua mạng.<br>
    • <span class="highlight-green">BF Semi-Join tối ưu</span>: Chỉ tốn <strong>${opt} KB</strong> — tiết kiệm <strong>${savedPct}%</strong> băng thông.<br>
  `;

  if (beMBits) {
    html += `
      • ⚡ <strong>Break-even Point</strong>: Tại <span style="color:#facc15; font-weight:700;">m = ${beMBits} bits</span> 
        (≈ ${beKB} KB), BF Semi-Join bắt đầu rẻ hơn Naive Join.<br>
      • Vùng <span class="highlight-red">bên trái điểm gãy</span>: m quá nhỏ → FPR cao → gửi nhiều False Positive → không đáng dùng BF.<br>
      • Vùng <span class="highlight-green">bên phải điểm gãy</span>: m đủ lớn → FPR thấp → BF có lợi rõ rệt.
    `;
  } else {
    html += `• ✅ BF Semi-Join <span class="highlight-green">luôn tốt hơn</span> Naive Join trong mọi giá trị m được khảo sát — overlap đủ thấp để BF luôn có lợi.`;
  }

  text.innerHTML = html;
  box.style.display = 'flex';
}


async function runSimulation() {
  const numSubs   = parseInt(document.getElementById('slider-subs').value);
  const numLogs   = parseInt(document.getElementById('slider-logs').value);
  const overlap   = parseInt(document.getElementById('slider-overlap').value) / 100;

  const switchNodeB = document.getElementById('switch-node-b');
  const nodeBOnline = switchNodeB ? switchNodeB.checked : true;

  // Show loading — fade in
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.remove('loading-overlay--hidden');
  // Nếu offline thì chạy animation loading ngắn hơn vì API sẽ trả về lỗi nhanh
  startLoadingAnimation(nodeBOnline ? 14000 : 3000);

  // Disable buttons
  document.getElementById('btn-run-demo')?.setAttribute('disabled', '');
  document.getElementById('btn-simulate')?.setAttribute('disabled', '');

  resetPipelineError();

  try {
    const res  = await fetch('/api/run-simulation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        num_subscribers: numSubs, 
        num_logs: numLogs, 
        overlap_ratio: overlap,
        node_b_online: nodeBOnline
      })
    });

    // Nếu sập Node B và API trả về lỗi
    if (!res.ok && !nodeBOnline) {
      const errorData = await res.json().catch(() => ({}));
      finishLoadingAnimation();
      await sleep(400);
      overlay.classList.add('loading-overlay--hidden');

      // Chạy hiệu ứng lỗi kết nối trên pipeline
      handlePipelineConnectionError();

      // Chuyển sang tab Pipeline để người dùng nhìn thấy hiệu ứng lỗi ngay lập tức
      switchTab('pipeline');

      setTimeout(() => {
        alert('GIAO DỊCH PHÂN TÁN BỊ HỦY BỎ (ABORTED)!\n\nLỗi mạng: ' + (errorData.error || 'Connection timed out: Node B is unreachable.'));
      }, 1400);
      return;
    }

    const data = await res.json();
    if (!data.success) { alert('Lỗi: ' + data.error); return; }

    finishLoadingAnimation();

    // Small delay to show 100% bar
    await sleep(500);

    // Update all UI
    updateHeroStats(data);
    updateCharts(data);
    updateTables(data);
    updateConclusion(data);
    renderBestResultCard(data);
    animatePipeline(data.results);

    // Show charts, hide placeholder
    document.getElementById('charts-section').classList.add('charts-visible');
    document.getElementById('charts-placeholder').style.display = 'none';

    // Chuyển sang tab dashboard
    setTimeout(() => {
      switchTab('dashboard');
    }, 300);

  } catch (err) {
    alert('Không thể kết nối server. Hãy chạy: python app.py');
    console.error(err);
  } finally {
    // Hide loading — fade out
    overlay.classList.add('loading-overlay--hidden');
    document.getElementById('btn-run-demo')?.removeAttribute('disabled');
    document.getElementById('btn-simulate')?.removeAttribute('disabled');
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ==========================================================
// UPDATE HERO STATS (with count-up)
// ==========================================================
function updateHeroStats(data) {
  const cfg   = data.config;
  const naive = data.results[0];
  const best  = data.results.reduce((a, b) => a.network_bytes < b.network_bytes ? a : b);
  const savePct = ((naive.network_bytes - best.network_bytes) / naive.network_bytes * 100).toFixed(1);

  countUp(document.getElementById('stat-subscribers'), fmtNum(cfg.num_subscribers));
  countUp(document.getElementById('stat-logs'),        fmtNum(cfg.num_logs));
  countUp(document.getElementById('stat-saving'),      savePct + '%');
  countUp(document.getElementById('stat-time'),        data.elapsed_seconds + 's');
}

// ==========================================================
// BEST RESULT CARD
// ==========================================================
function renderBestResultCard(data) {
  const naive  = data.results[0];
  const best   = data.results.reduce((a, b) => a.network_bytes < b.network_bytes ? a : b);
  const savePct = ((naive.network_bytes - best.network_bytes) / naive.network_bytes * 100).toFixed(1);

  document.getElementById('best-strategy-name').textContent = best.strategy;

  const metrics = [
    { value: savePct + '%',          label: 'Băng thông tiết kiệm', color: COLORS.bf1 },
    { value: fmtNum(best.final_rows),label: 'Kết quả (rows)',      color: COLORS.purple },
    { value: (best.savings_leverage || 0).toFixed(0) + 'x', label: 'Leverage',    color: COLORS.bf01 },
  ];

  document.getElementById('best-metrics').innerHTML = metrics.map(m => `
    <div class="best-metric-item">
      <div class="best-metric-value" style="color:${m.color}">${m.value}</div>
      <div class="best-metric-label">${m.label}</div>
    </div>
  `).join('');

  document.getElementById('best-result-section').classList.add('visible');
}

// ==========================================================
// UPDATE CHARTS
// ==========================================================
function updateCharts(data) {
  drawBandwidthChart(data.results);
  drawFprChart(data.results);
}

function drawBandwidthChart(results) {
  const ctx = document.getElementById('chart-bandwidth').getContext('2d');
  if (chartBandwidth) chartBandwidth.destroy();

  const labels = results.map(r => r.strategy.replace('BF Semi-Join', 'BF').replace(' (FPR ', '\n(FPR '));
  const values = results.map(r => r.network_kb);
  const colors = CHART_COLORS.slice(0, results.length);

  chartBandwidth = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Băng thông (KB)',
        data: values,
        backgroundColor: colors.map(c => c + 'bb'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 10,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => {
              const naive = values[0];
              const saving = ((naive - ctx.raw) / naive * 100).toFixed(1);
              return ctx.dataIndex > 0 ? `Tiết kiệm: ${saving}%` : 'Baseline (100%)';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: COLORS.grid },
          title: { display: true, text: 'KB', color: COLORS.muted }
        },
        x: { grid: { display: false }, ticks: { font: { size: 9 } } }
      },
      animation: { duration: 1400, easing: 'easeOutQuart' }
    }
  });
}

function drawFprChart(results) {
  const ctx = document.getElementById('chart-fpr').getContext('2d');
  if (chartFpr) chartFpr.destroy();

  const bfResults  = results.filter(r => r.fpr_target !== undefined);
  const fprTargets = bfResults.map(r => (r.fpr_target * 100).toFixed(1) + '%');
  const fprTheory  = bfResults.map(r => r.fpr_target * 100);
  const fprActual  = bfResults.map(r =>
    r.rows_transferred > 0 ? (r.false_positives / r.rows_transferred * 100) : 0
  );

  chartFpr = new Chart(ctx, {
    type: 'line',
    data: {
      labels: fprTargets,
      datasets: [
        {
          label: 'FPR Lý thuyết (setup)',
          data: fprTheory,
          borderColor: COLORS.purple,
          backgroundColor: COLORS.purple + '25',
          pointBackgroundColor: COLORS.purple,
          borderWidth: 2,
          pointRadius: 7,
          borderDash: [7, 4],
          tension: 0.35,
          fill: false,
        },
        {
          label: 'FP Thực tế (đo được)',
          data: fprActual,
          borderColor: COLORS.bf1,
          backgroundColor: COLORS.bf1 + '20',
          pointBackgroundColor: COLORS.bf1,
          borderWidth: 2,
          pointRadius: 7,
          tension: 0.35,
          fill: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, padding: 18 } },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: COLORS.grid }, title: { display: true, text: '%', color: COLORS.muted } },
        x: { grid: { color: COLORS.grid } }
      },
      animation: { duration: 1400 }
    }
  });
}

function initOverlapChart() {
  const ctx = document.getElementById('chart-overlap').getContext('2d');
  const labels = [], match = [], waste = [];
  for (let i = 5; i <= 95; i += 5) {
    labels.push(i + '%');
    match.push(i);
    waste.push(100 - i);
  }
  chartOverlap = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Dữ liệu cần (match)',
          data: match,
          backgroundColor: COLORS.bf1 + '55',
          borderColor: COLORS.bf1,
          borderWidth: 2,
          fill: true, tension: 0.4, pointRadius: 0,
        },
        {
          label: 'Dữ liệu lãng phí',
          data: waste,
          backgroundColor: COLORS.naive + '44',
          borderColor: COLORS.naive,
          borderWidth: 2,
          fill: true, tension: 0.4, pointRadius: 0,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 16 } } },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: COLORS.grid }, title: { display: true, text: '%', color: COLORS.muted } },
        x: { grid: { color: COLORS.grid }, title: { display: true, text: 'Overlap Ratio', color: COLORS.muted } }
      },
      animation: { duration: 1000 }
    }
  });
}

function initBfSizeChart() {
  fetch('/api/bf-size-data')
    .then(r => r.json())
    .then(data => {
      const ctx = document.getElementById('chart-bfsize').getContext('2d');
      const lineColors = [COLORS.bf10, COLORS.bf5, COLORS.bf1, COLORS.bf01];
      const datasets = Object.entries(data.datasets).map(([label, sizes], i) => ({
        label,
        data: sizes,
        borderColor: lineColors[i],
        backgroundColor: lineColors[i] + '18',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.4,
        fill: false,
      }));
      chartBfSize = new Chart(ctx, {
        type: 'line',
        data: { labels: data.n_values.map(v => v.toFixed(0) + 'K'), datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 16 } } },
          scales: {
            y: { beginAtZero: true, grid: { color: COLORS.grid }, title: { display: true, text: 'MB', color: COLORS.muted } },
            x: { grid: { display: false }, title: { display: true, text: 'Số phần tử (nghìn)', color: COLORS.muted }, ticks: { maxTicksLimit: 12, font: { size: 9 } } }
          },
          animation: { duration: 1000 }
        }
      });
    })
    .catch(() => drawBfSizeLocal());
}

function drawBfSizeLocal() {
  const ctx = document.getElementById('chart-bfsize').getContext('2d');
  const nVals = [];
  for (let n = 1000; n <= 1000000; n += 20000) nVals.push(n);
  const fprs = [0.10, 0.05, 0.01, 0.001];
  const lineColors = [COLORS.bf10, COLORS.bf5, COLORS.bf1, COLORS.bf01];
  const datasets = fprs.map((fpr, i) => ({
    label: `FPR ${(fpr * 100).toFixed(1)}%`,
    data: nVals.map(n => {
      const m = Math.ceil(-(n * Math.log(fpr)) / (Math.log(2) ** 2));
      return m / 8 / 1024 / 1024;
    }),
    borderColor: lineColors[i],
    borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false,
  }));
  chartBfSize = new Chart(ctx, {
    type: 'line',
    data: { labels: nVals.map(v => (v / 1000).toFixed(0) + 'K'), datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { usePointStyle: true } } },
      scales: {
        y: { beginAtZero: true, grid: { color: COLORS.grid }, title: { display: true, text: 'MB' } },
        x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 9 } } }
      }
    }
  });
}

// ==========================================================
// UPDATE TABLES
// ==========================================================
function updateTables(data) {
  const results    = data.results;
  const naive      = results[0];
  const naiveBytes = naive.network_bytes;
  const bestBytes  = Math.min(...results.map(r => r.network_bytes));

  // Strategy badge colors
  const strategyColor = [COLORS.naive, COLORS.bf10, COLORS.bf5, COLORS.bf1, COLORS.bf01];

  // ── Table 1: Bandwidth ──
  let html1 = '';
  results.forEach((r, i) => {
    const isBest = r.network_bytes === bestBytes && i > 0;
    const cls = i === 0 ? 'row-naive' : (isBest ? 'row-best' : '');
    const savStr = r.saving_pct > 0
      ? `<div class="savings-bar-wrap">
           <span class="hl-green">${r.saving_pct}%</span>
           <div class="savings-bar" style="width:${Math.min(r.saving_pct, 100) * 0.8}px"></div>
         </div>`
      : '<span style="color:var(--text-muted)">baseline</span>';
    html1 += `<tr class="${cls}" style="animation-delay:${i * 80}ms">
      <td><span class="strategy-badge" style="background:${strategyColor[i]}22;color:${strategyColor[i]};border:1px solid ${strategyColor[i]}44">${i === 0 ? 'NAIVE' : `BF ${i}`}</span>${r.strategy}</td>
      <td>${fmtNum(r.rows_transferred)}</td>
      <td class="${r.false_positives > 0 ? 'hl-orange' : ''}">${fmtNum(r.false_positives)}</td>
      <td class="${isBest ? 'hl-green' : (i === 0 ? 'hl-pink' : '')}">${fmtNum(r.network_kb)} KB</td>
      <td>${savStr}</td>
    </tr>`;
  });
  document.getElementById('tbody-bandwidth').innerHTML = html1;

  // ── Table 2: Bytes Saved ──
  let html2 = '';
  results.forEach((r, i) => {
    const isBest = r.network_bytes === bestBytes && i > 0;
    const cls = i === 0 ? 'row-naive' : (isBest ? 'row-best' : '');
    if (i === 0) {
      html2 += `<tr class="${cls}" style="animation-delay:${i * 80}ms">
        <td><span class="strategy-badge" style="background:${strategyColor[i]}22;color:${strategyColor[i]};border:1px solid ${strategyColor[i]}44">NAIVE</span>${r.strategy}</td>
        <td class="hl-pink">N/A</td><td class="hl-pink">N/A</td><td class="hl-pink">N/A</td><td class="hl-pink">N/A</td>
      </tr>`;
    } else {
      html2 += `<tr class="${cls}" style="animation-delay:${i * 80}ms">
        <td><span class="strategy-badge" style="background:${strategyColor[i]}22;color:${strategyColor[i]};border:1px solid ${strategyColor[i]}44">BF ${i}</span>${r.strategy}</td>
        <td class="hl-cyan">${fmtNum(r.bf_size_bits)}</td>
        <td>${r.bf_size_kb} KB</td>
        <td class="hl-green">${fmtNum(r.bytes_saved_kb)} KB</td>
        <td class="${isBest ? 'hl-purple' : ''}">${r.savings_leverage}x</td>
      </tr>`;
    }
  });
  document.getElementById('tbody-bytes-saved').innerHTML = html2;

  // ── Table 3: FPR Impact ──
  let html3 = '';
  results.forEach((r, i) => {
    const isBest = r.network_bytes === bestBytes && i > 0;
    const cls = i === 0 ? 'row-naive' : (isBest ? 'row-best' : '');
    if (i === 0) {
      html3 += `<tr class="${cls}" style="animation-delay:${i * 80}ms">
        <td><span class="strategy-badge" style="background:${strategyColor[i]}22;color:${strategyColor[i]};border:1px solid ${strategyColor[i]}44">NAIVE</span>${r.strategy}</td>
        <td class="hl-pink">N/A</td><td>0</td><td>0</td><td class="hl-pink">N/A</td>
      </tr>`;
    } else {
      html3 += `<tr class="${cls}" style="animation-delay:${i * 80}ms">
        <td><span class="strategy-badge" style="background:${strategyColor[i]}22;color:${strategyColor[i]};border:1px solid ${strategyColor[i]}44">BF ${i}</span>${r.strategy}</td>
        <td>${(r.fpr_target * 100).toFixed(1)}%</td>
        <td class="hl-orange">${fmtNum(r.false_positives)}</td>
        <td>${r.fp_extra_kb} KB</td>
        <td class="hl-cyan">${r.num_hash_functions}</td>
      </tr>`;
    }
  });
  document.getElementById('tbody-fpr-impact').innerHTML = html3;
}

// ==========================================================
// UPDATE CONCLUSION
// ==========================================================
function updateConclusion(data) {
  const results = data.results;
  const naive   = results[0];
  const best    = results.reduce((a, b) => a.network_bytes < b.network_bytes ? a : b);
  const savPct  = ((naive.network_bytes - best.network_bytes) / naive.network_bytes * 100).toFixed(1);

  const dot = (color) => `<span class="cl-dot cl-dot--${color}"></span>`;

  const html = `
    <p>${dot('teal')}  <strong>Chiến lược tối ưu:</strong>&nbsp; ${best.strategy}</p>
    <p>${dot('cyan')}  <strong>Bandwidth:</strong>&nbsp; ${fmtNum(naive.network_kb)} KB → ${fmtNum(best.network_kb)} KB — tiết kiệm <strong>${savPct}%</strong></p>
    <p>${dot('purple')}<strong>BF Size (m):</strong>&nbsp; ${fmtNum(best.bf_size_bits || 0)} bits = ${best.bf_size_kb || 0} KB</p>
    <p>${dot('green')} <strong>Savings Leverage:</strong>&nbsp; ${best.savings_leverage || 0}x &mdash; 1 byte BF → tiết kiệm ${best.savings_leverage || 0} bytes</p>
    <p>${dot('green')} <strong>Kết quả:</strong>&nbsp; ${fmtNum(naive.final_rows)} dòng &mdash; chính xác 100% (FP bị loại ở Inner Join cuối)</p>
    <p>${dot('orange')}<strong>False Negative = 0%</strong>&nbsp; &mdash; BF tuyệt đối không bỏ sót subscriber thật</p>
  `;
  document.getElementById('conclusion-content').innerHTML = html;
  document.getElementById('conclusion-card').classList.add('visible');
}

// ==========================================================
// THEORETICAL ANALYSIS
// ==========================================================
async function runTheoretical() {
  const container = document.getElementById('theory-results');
  container.innerHTML = '<p style="color:var(--purple);font-size:0.85rem;margin-top:12px">Đang tính toán...</p>';
  try {
    const res  = await fetch('/api/theoretical', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_subscribers: 1000000, num_logs: 10000000, overlap_ratio: 0.20 })
    });
    const data = await res.json();
    if (!data.success) { container.innerHTML = '<p style="color:var(--pink)">Lỗi: ' + data.error + '</p>'; return; }

    let html = `<p style="margin:12px 0 10px;color:var(--teal);font-size:0.83rem">
      Naive Join: <strong>${data.config.naive_mb} MB</strong> phải truyền qua mạng
    </p>`;
    html += '<table><thead><tr><th>FPR</th><th>m (bits)</th><th>BF (MB)</th><th>Total (MB)</th><th>Saved</th><th>%</th><th>Leverage</th></tr></thead><tbody>';
    data.results.forEach(r => {
      html += `<tr>
        <td>${r.fpr_pct.toFixed(1)}%</td>
        <td class="hl-cyan">${fmtNum(r.m_bits)}</td>
        <td>${r.bf_mb}</td>
        <td>${r.total_mb}</td>
        <td class="hl-green">${r.saved_mb} MB</td>
        <td class="hl-green">${r.saved_pct}%</td>
        <td class="hl-purple">${r.leverage}x</td>
      </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  } catch {
    container.innerHTML = '<p style="color:var(--pink)">Không thể kết nối server.</p>';
  }
}

// ==========================================================
// DISTRIBUTED — 2 Processes (Site A ↔ Site B)
// ==========================================================

async function checkSiteBStatus() {
  const el = document.getElementById('dist-site-b-status');
  if (!el) return;
  el.textContent = '● Checking...';
  el.className = 'dist-node-status checking';
  try {
    const res = await fetch('/api/run-distributed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_subscribers: 1, num_logs: 1, overlap_ratio: 0.5, fpr_target: 0.1, _healthcheck: true })
    });
    // We just check if site B is reachable via our proxy
    const statusRes = await fetch('http://localhost:5001/api/status', { mode: 'no-cors' }).catch(() => null);
    // Since no-cors, we can't read the response, but if it doesn't throw, it's likely online
    el.textContent = '● Online';
    el.className = 'dist-node-status online';
  } catch {
    el.textContent = '● Offline';
    el.className = 'dist-node-status offline';
  }

  const elA = document.getElementById('dist-site-a-status');
  if (elA) { elA.textContent = '● Online'; elA.className = 'dist-node-status online'; }
}

async function runDistributed() {
  const nSubs = parseInt(document.getElementById('dist-subs').value) || 10000;
  const nLogs = parseInt(document.getElementById('dist-logs').value) || 50000;
  const fpr   = (parseFloat(document.getElementById('dist-fpr').value) || 1) / 100;

  const btn = document.getElementById('btn-distributed');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Đang chạy...'; }

  const timeline = document.getElementById('dist-timeline');
  timeline.innerHTML = '<p style="color:var(--teal); text-align:center;">🔄 Đang kết nối Site B...</p>';

  try {
    const res = await fetch('/api/run-distributed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num_subscribers: nSubs,
        num_logs: nLogs,
        overlap_ratio: 0.20,
        fpr_target: fpr
      })
    });

    const data = await res.json();

    if (!data.success) {
      timeline.innerHTML = `<p style="color:#f87171; text-align:center;">❌ ${data.error}</p>`;
      const elB = document.getElementById('dist-site-b-status');
      if (elB) { elB.textContent = '● Offline'; elB.className = 'dist-node-status offline'; }
      return;
    }

    // Update Site B status
    const elB = document.getElementById('dist-site-b-status');
    if (elB) { elB.textContent = '● Online'; elB.className = 'dist-node-status online'; }
    const elA = document.getElementById('dist-site-a-status');
    if (elA) { elA.textContent = '● Online'; elA.className = 'dist-node-status online'; }

    // Render timeline
    timeline.innerHTML = '';
    data.timeline.forEach((item, idx) => {
      const div = document.createElement('div');
      div.className = 'dist-tl-item done';
      div.style.animationDelay = `${idx * 120}ms`;
      div.innerHTML = `
        <div class="dist-tl-step">Bước ${item.step}</div>
        <div style="flex:1;">
          <div class="dist-tl-label">${item.label}</div>
          <div class="dist-tl-detail">${item.detail}</div>
        </div>
        <div class="dist-tl-time">${item.time_ms} ms</div>
      `;
      timeline.appendChild(div);
    });

    // Show result card
    const resultCard = document.getElementById('dist-result-card');
    if (resultCard) {
      resultCard.style.display = 'block';
      const r = data.results;
      document.getElementById('dist-result-grid').innerHTML = `
        <div class="be-info-card glass-card">
          <div class="be-info-icon" style="color:#f87171;">📦</div>
          <div class="be-info-label">Naive Join</div>
          <div class="be-info-value">${fmtNum(Math.round(r.naive_cost_kb))} KB</div>
          <div class="be-info-sub">Gửi toàn bộ ${fmtNum(r.rows_sent_to_b)} logs</div>
        </div>
        <div class="be-info-card glass-card">
          <div class="be-info-icon" style="color:#818cf8;">🔍</div>
          <div class="be-info-label">BF Semi-Join</div>
          <div class="be-info-value">${fmtNum(Math.round(r.bf_cost_kb))} KB</div>
          <div class="be-info-sub">BF: ${fmtNum(r.bf_m_bits)} bits (k=${r.bf_k})</div>
        </div>
        <div class="be-info-card glass-card">
          <div class="be-info-icon" style="color:#34d399;">💰</div>
          <div class="be-info-label">Tiết kiệm</div>
          <div class="be-info-value text-green">${r.saving_pct}%</div>
          <div class="be-info-sub">Loại ${fmtNum(r.rows_rejected_at_b)} dòng tại B</div>
        </div>
        <div class="be-info-card glass-card">
          <div class="be-info-icon" style="color:#facc15;">⏱️</div>
          <div class="be-info-label">Tổng thời gian</div>
          <div class="be-info-value">${r.total_time_ms} ms</div>
          <div class="be-info-sub">FP=${fmtNum(r.false_positives)}, Join=${fmtNum(r.final_join_rows)}</div>
        </div>
      `;

      // Update connection label
      const connLabel = document.getElementById('dist-conn-label');
      if (connLabel) connLabel.textContent = `${r.total_time_ms}ms round-trip`;
    }

  } catch (err) {
    timeline.innerHTML = `<p style="color:#f87171; text-align:center;">❌ Lỗi: ${err.message}</p>`;
    console.error(err);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<span class="btn-shine"></span>🚀 Chạy Phân Tán'; }
  }
}


// ==========================================================
// SENSITIVITY ANALYSIS — Overlap Slider (Ưu tiên 4)
// ==========================================================

let chartSensitivity = null;
let sensitivityData = null;  // Cache data from API

function initSensitivitySlider() {
  const slider = document.getElementById('sa-overlap-slider');
  if (!slider) return;

  slider.addEventListener('input', () => {
    const val = slider.value;
    document.getElementById('sa-overlap-val').textContent = val + '%';
    updateSensitivityDisplay(parseInt(val));
  });

  // Load data on first interaction
  slider.addEventListener('input', loadSensitivityData, { once: true });
}

async function loadSensitivityData() {
  try {
    const res = await fetch('/api/sensitivity-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_subscribers: 10000, num_logs: 100000, fpr_target: 0.01 })
    });
    const data = await res.json();
    if (!data.success) return;

    sensitivityData = data;
    renderSensitivityChart(data);
    updateSensitivityDisplay(20); // Default overlap
  } catch (e) {
    console.error('Sensitivity load error:', e);
  }
}

function updateSensitivityDisplay(overlapPct) {
  if (!sensitivityData) return;

  const idx = sensitivityData.overlaps.indexOf(overlapPct);
  if (idx < 0) return;

  document.getElementById('sa-saving-val').textContent = sensitivityData.savings_pct[idx] + '%';
  document.getElementById('sa-waste-val').textContent = sensitivityData.wasted_naive_pct[idx] + '%';
  document.getElementById('sa-bf-cost-val').textContent = fmtNum(Math.round(sensitivityData.bf_costs_kb[idx])) + ' KB';

  // Highlight current point on chart
  if (chartSensitivity) {
    const datasets = chartSensitivity.data.datasets;
    // Update point radius to highlight current
    datasets[0].pointRadius = sensitivityData.overlaps.map((_, i) => i === idx ? 6 : 0);
    datasets[0].pointBackgroundColor = sensitivityData.overlaps.map((_, i) => i === idx ? '#facc15' : COLORS.bf1);
    chartSensitivity.update('none');
  }

  // Update insight text
  const insight = document.getElementById('sa-insight');
  if (insight) {
    const saving = sensitivityData.savings_pct[idx];
    const waste = sensitivityData.wasted_naive_pct[idx];
    if (overlapPct <= 30) {
      insight.innerHTML = `<strong>Overlap ${overlapPct}%:</strong> BF Semi-Join cực kỳ hiệu quả — tiết kiệm <strong>${saving}%</strong> băng thông. Naive Join lãng phí ${waste}% dữ liệu truyền đi. Đây là kịch bản lý tưởng cho Bloom Filter.`;
    } else if (overlapPct <= 60) {
      insight.innerHTML = `<strong>Overlap ${overlapPct}%:</strong> BF Semi-Join vẫn có lợi — tiết kiệm <strong>${saving}%</strong>. Tuy nhiên lợi ích giảm dần vì lượng dữ liệu trùng khớp tăng → ít rows bị loại hơn tại Site B.`;
    } else {
      insight.innerHTML = `<strong>Overlap ${overlapPct}%:</strong> BF Semi-Join tiết kiệm <strong>${saving}%</strong>. Với overlap cao, hầu hết WebLogs đều thuộc subscribers → BF chỉ loại ít dữ liệu. Chi phí BF (${sensitivityData.config.bf_size_kb} KB) trở nên ít đáng kể.`;
    }
  }
}

function renderSensitivityChart(data) {
  if (chartSensitivity) chartSensitivity.destroy();
  const ctx = document.getElementById('chart-sensitivity');
  if (!ctx) return;

  chartSensitivity = new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: {
      labels: data.overlaps.map(v => v + '%'),
      datasets: [
        {
          label: 'BF Saving (%)',
          data: data.savings_pct,
          borderColor: COLORS.bf1,
          borderWidth: 2.5,
          fill: {
            target: 'origin',
            above: 'rgba(0, 232, 135, 0.08)'
          },
          tension: 0.4,
          pointRadius: 0,
          yAxisID: 'y',
        },
        {
          label: 'Naive Cost (KB)',
          data: data.naive_costs_kb,
          borderColor: COLORS.naive,
          borderWidth: 1.5,
          borderDash: [6, 3],
          pointRadius: 0,
          fill: false,
          tension: 0,
          yAxisID: 'y1',
        },
        {
          label: 'BF Cost (KB)',
          data: data.bf_costs_kb,
          borderColor: COLORS.purple,
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.3,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true, position: 'top',
          labels: { color: '#9aa3bc', font: { size: 11 }, boxWidth: 20, padding: 12 }
        },
        tooltip: {
          backgroundColor: 'rgba(16,16,30,0.95)',
          borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1,
          titleColor: '#e2e8f4', bodyColor: '#9aa3bc', padding: 10,
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Overlap Ratio', color: '#5a6080', font: { size: 11 } },
          ticks: { color: '#5a6080', font: { size: 10 } },
          grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
          type: 'linear', position: 'left',
          title: { display: true, text: 'BF Saving (%)', color: COLORS.bf1, font: { size: 11 } },
          ticks: { color: COLORS.bf1, font: { size: 10 }, callback: v => v + '%' },
          grid: { color: 'rgba(255,255,255,0.04)' },
          min: 0, max: 100,
        },
        y1: {
          type: 'linear', position: 'right',
          title: { display: true, text: 'Network Cost (KB)', color: '#5a6080', font: { size: 11 } },
          ticks: { color: '#5a6080', font: { size: 10 }, callback: v => fmtNum(Math.round(v)) },
          grid: { display: false },
        }
      }
    }
  });
}


// ==========================================================
// HELPERS
// ==========================================================
function fmtNum(n) { return Number(n).toLocaleString(); }

// Initialize: hide charts grid, show placeholder
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('charts-section').style.display = 'none';
  initSensitivitySlider();
});
