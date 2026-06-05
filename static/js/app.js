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
  initOverlapChart();
  initBfSizeChart();
  // Khởi tạo tab navigation
  switchTab('hero');
});

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

// ==========================================================
// RUN SIMULATION
// ==========================================================
async function runSimulation() {
  const numSubs   = parseInt(document.getElementById('slider-subs').value);
  const numLogs   = parseInt(document.getElementById('slider-logs').value);
  const overlap   = parseInt(document.getElementById('slider-overlap').value) / 100;

  // Show loading — fade in
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.remove('loading-overlay--hidden');
  startLoadingAnimation(14000);

  // Disable buttons
  document.getElementById('btn-run-demo')?.setAttribute('disabled', '');
  document.getElementById('btn-simulate')?.setAttribute('disabled', '');

  try {
    const res  = await fetch('/api/run-simulation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_subscribers: numSubs, num_logs: numLogs, overlap_ratio: overlap })
    });
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
// HELPERS
// ==========================================================
function fmtNum(n) { return Number(n).toLocaleString(); }

// Initialize: hide charts grid, show placeholder
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('charts-section').style.display = 'none';
});
