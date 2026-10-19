/**
 * LedgerLens Frontend Application Logic.
 * Orchestrates UI interactions, Mastra workflow triggering, editable spreadsheet,
 * and Chart.js forecast visualization.
 */

let currentTransactions = [];
let forecastChartInstance = null;
let selectedFile = null;
let selectedSamplePath = null;

document.addEventListener('DOMContentLoaded', () => {
  initPrivacyStatus();
  loadSamples();
  setupUploadHandlers();
  setupPipelineButton();
  setupTableActions();
  setupForecastActions();
  loadStoredTransactions();
});

// 1. Privacy & TabPFN Status
async function initPrivacyStatus() {
  try {
    const res = await fetch('/api/backend/privacy-status');
    if (!res.ok) return;
    const data = await res.json();
    
    document.getElementById('visionModelStatus').textContent = `${data.ollama_model} (${data.ollama_endpoint})`;
    document.getElementById('tabpfnModelStatus').textContent = `${data.tabpfn_mode}`;
    document.getElementById('egressStatus').textContent = data.data_egress_status;
    
    const toggle = document.getElementById('tabpfnToggle');
    toggle.checked = data.tabpfn_api_enabled;
    updateToggleLabels(data.tabpfn_api_enabled);

    toggle.addEventListener('change', async (e) => {
      const enable = e.target.checked;
      const tRes = await fetch(`/api/backend/toggle-tabpfn-api?enable=${enable}`, { method: 'POST' });
      if (tRes.ok) {
        const tData = await tRes.json();
        updateToggleLabels(tData.enable_tabpfn_api);
        initPrivacyStatus();
      }
    });
  } catch (err) {
    console.error('Failed to load privacy status:', err);
  }
}

function updateToggleLabels(isApiEnabled) {
  const lbl = document.getElementById('tabpfnToggleLabel');
  const badge = document.getElementById('tabpfnBadge');
  const note = document.getElementById('privacyNote');
  
  if (isApiEnabled) {
    lbl.innerHTML = 'TabPFN Mode: <strong>CLIENT (Cloud API - Anonymized)</strong>';
    badge.textContent = 'Cloud API (Numeric Only)';
    badge.className = 'sub-badge blue-badge';
    note.innerHTML = '⚠️ <strong>TabPFN Cloud API Enabled:</strong> Only anonymized numerical matrices (day indices and amounts) are transmitted. Customer names, Hindi ledger descriptions, and personal data <strong>never</strong> leave your device.';
  } else {
    lbl.innerHTML = 'TabPFN Mode: <strong>LOCAL (On-Device CPU)</strong>';
    badge.textContent = 'On-Device CPU';
    badge.className = 'sub-badge green-badge';
    note.innerHTML = '🛡️ <strong>Zero-Cloud Guarantee:</strong> All vision extraction, anomaly detection, and cash-flow forecasting run 100% locally on your machine. Customer financial data never touches the cloud.';
  }
}

// 2. Load Sample Ledger Images
async function loadSamples() {
  const select = document.getElementById('sampleSelect');
  try {
    const res = await fetch('/api/samples');
    if (!res.ok) return;
    const samples = await res.json();
    
    samples.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.path;
      opt.textContent = s.name.replace(/_/g, ' ').replace('.png', '').toUpperCase();
      select.appendChild(opt);
    });

    select.addEventListener('change', (e) => {
      if (e.target.value) {
        selectedSamplePath = e.target.value;
        selectedFile = null;
        const chosen = samples.find(s => s.path === e.target.value);
        if (chosen) showPreview(chosen.url, chosen.name);
        document.getElementById('runPipelineBtn').disabled = false;
      }
    });
  } catch (err) {
    console.error('Failed to load samples:', err);
  }
}

// 3. Upload & Drag-Drop Handling
function setupUploadHandlers() {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');

  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  selectedFile = file;
  selectedSamplePath = null;
  document.getElementById('sampleSelect').value = '';
  
  const reader = new FileReader();
  reader.onload = (e) => {
    showPreview(e.target.result, file.name);
    document.getElementById('runPipelineBtn').disabled = false;
  };
  reader.readAsDataURL(file);
}

function showPreview(src, name) {
  document.getElementById('dropContent').classList.add('hidden');
  const prevContent = document.getElementById('previewContent');
  prevContent.classList.remove('hidden');
  document.getElementById('imagePreview').src = src;
  document.getElementById('imagePreviewName').textContent = `Selected: ${name}`;
}

// 4. Run Mastra Pipeline
function setupPipelineButton() {
  const btn = document.getElementById('runPipelineBtn');
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = '⏳ Processing Workflow...';

    resetStepTracker();
    setStepState('step-extract', 'active');

    const formData = new FormData();
    if (selectedFile) {
      formData.append('image', selectedFile);
    } else if (selectedSamplePath) {
      formData.append('samplePath', selectedSamplePath);
    } else {
      alert('Please select or upload an image first.');
      btn.disabled = false;
      btn.textContent = '⚡ Run Mastra Workflow Pipeline';
      return;
    }

    try {
      // Simulate step progression animation while workflow executes
      setTimeout(() => setStepState('step-validate', 'active'), 2500);
      setTimeout(() => setStepState('step-store', 'active'), 3200);
      setTimeout(() => setStepState('step-forecast', 'active'), 3800);
      setTimeout(() => setStepState('step-summarize', 'active'), 4500);

      const res = await fetch('/api/pipeline/run', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Pipeline execution failed');
      }

      const responseData = await res.json();
      const payload = responseData.data?.result || responseData.data || {};

      // Complete steps in UI
      completeAllSteps();

      // Display observability latency
      loadObservabilityMetrics();

      // Load results into UI
      await loadStoredTransactions();

      if (payload.summary) {
        renderSummaryCard(payload.summary);
      }
      if (payload.anomalies) {
        renderAnomalies(payload.anomalies);
      }
      if (payload.forecast) {
        renderForecastChart(payload.forecast);
      }

    } catch (err) {
      alert(`Workflow failed: ${err.message}`);
      console.error(err);
    } finally {
      btn.disabled = false;
      btn.textContent = '⚡ Run Mastra Workflow Pipeline';
    }
  });
}

function resetStepTracker() {
  ['step-extract', 'step-validate', 'step-store', 'step-forecast', 'step-summarize'].forEach(id => {
    const el = document.getElementById(id);
    el.className = 'step-item';
  });
}

function setStepState(stepId, state) {
  const el = document.getElementById(stepId);
  if (el) el.className = `step-item ${state}`;
}

function completeAllSteps() {
  ['step-extract', 'step-validate', 'step-store', 'step-forecast', 'step-summarize'].forEach(id => {
    setStepState(id, 'completed');
  });
}

// 5. Observability
async function loadObservabilityMetrics() {
  try {
    const res = await fetch('/api/backend/observability');
    if (!res.ok) return;
    const data = await res.json();
    const obsBar = document.getElementById('obsBar');
    obsBar.classList.remove('hidden');

    const steps = data.by_step || {};
    document.getElementById('obsExtract').textContent = `Extract: ${steps.extract?.avg_ms || 0}ms`;
    document.getElementById('obsValidate').textContent = `Validate: ${steps.validate?.avg_ms || 0}ms`;
    document.getElementById('obsStore').textContent = `Store: ${steps.store?.avg_ms || 0}ms`;
    document.getElementById('obsForecast').textContent = `Forecast: ${steps.forecast?.avg_ms || 0}ms`;
    document.getElementById('obsTotal').textContent = `Total Steps Logged: ${data.total_steps}`;
  } catch (err) {
    console.error('Failed to load observability metrics:', err);
  }
}

// 6. Editable Transactions Table
async function loadStoredTransactions() {
  try {
    const [txRes, anomRes, fcRes, sumRes] = await Promise.all([
      fetch('/api/backend/transactions'),
      fetch('/api/backend/anomalies', { method: 'POST' }),
      fetch('/api/backend/forecast?days=30', { method: 'POST' }),
      fetch('/api/backend/summarize', { method: 'POST' })
    ]);

    if (txRes.ok) {
      currentTransactions = await txRes.json();
      renderTransactionsTable(currentTransactions);
    }
    if (anomRes.ok) {
      renderAnomalies(await anomRes.json());
    }
    if (fcRes.ok) {
      renderForecastChart(await fcRes.json());
    }
    if (sumRes.ok) {
      renderSummaryCard(await sumRes.json());
    }
  } catch (err) {
    console.error('Failed to load stored transactions:', err);
  }
}

function renderTransactionsTable(transactions) {
  const tbody = document.getElementById('transactionsBody');
  tbody.innerHTML = '';

  if (!transactions || transactions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No transactions yet. Scan a ledger image or load demo data below.</td></tr>';
    return;
  }

  transactions.forEach((tx, idx) => {
    const tr = document.createElement('tr');
    const isLowConfidence = parseFloat(tx.confidence) < 0.7 || tx.flagged;
    if (isLowConfidence) {
      tr.className = 'row-review';
    }

    const reviewBadge = isLowConfidence
      ? `<span class="badge-review">⚠️ Review (${parseFloat(tx.confidence).toFixed(2)})</span>`
      : `<span class="badge-ok">✓ Confident (${parseFloat(tx.confidence).toFixed(2)})</span>`;

    tr.innerHTML = `
      <td><input type="date" value="${tx.date || ''}" data-field="date" data-idx="${idx}"></td>
      <td><input type="text" value="${escapeHtml(tx.party || '')}" data-field="party" data-idx="${idx}"></td>
      <td><input type="text" value="${escapeHtml(tx.item || '')}" data-field="item" data-idx="${idx}"></td>
      <td><input type="number" step="0.5" value="${tx.quantity || 1.0}" data-field="quantity" data-idx="${idx}"></td>
      <td><input type="number" step="0.01" value="${tx.amount || 0.0}" data-field="amount" data-idx="${idx}"></td>
      <td>
        <select data-field="type" data-idx="${idx}">
          <option value="sale" ${tx.type === 'sale' ? 'selected' : ''}>Sale (जमा)</option>
          <option value="expense" ${tx.type === 'expense' ? 'selected' : ''}>Expense (खर्च)</option>
        </select>
      </td>
      <td><input type="number" step="0.05" min="0" max="1" value="${tx.confidence || 1.0}" data-field="confidence" data-idx="${idx}"></td>
      <td>
        ${reviewBadge}
        ${tx.flag_reason ? `<br><small style="color: #b45309;">${escapeHtml(tx.flag_reason)}</small>` : ''}
      </td>
      <td><button class="btn-delete-row" data-idx="${idx}" title="Delete row">✕</button></td>
    `;
    tbody.appendChild(tr);
  });

  // Attach change listeners to inputs
  tbody.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('change', (e) => {
      const idx = e.target.getAttribute('data-idx');
      const field = e.target.getAttribute('data-field');
      let val = e.target.value;
      if (['quantity', 'amount', 'confidence'].includes(field)) {
        val = parseFloat(val) || 0;
      }
      currentTransactions[idx][field] = val;
    });
  });

  // Attach delete buttons
  tbody.querySelectorAll('.btn-delete-row').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.getAttribute('data-idx'), 10);
      currentTransactions.splice(idx, 1);
      renderTransactionsTable(currentTransactions);
    });
  });
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// 7. Table Actions: Add, Save, Download CSV/XLSX, Clear
function setupTableActions() {
  document.getElementById('addRowBtn').addEventListener('click', () => {
    const today = new Date().toISOString().split('T')[0];
    currentTransactions.unshift({
      date: today,
      party: 'New Customer',
      item: 'Description',
      quantity: 1.0,
      amount: 100.0,
      currency: 'INR',
      type: 'sale',
      confidence: 1.0,
      flagged: false,
      flag_reason: null
    });
    renderTransactionsTable(currentTransactions);
  });

  document.getElementById('saveTableBtn').addEventListener('click', async () => {
    try {
      const res = await fetch('/api/backend/store', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentTransactions)
      });
      if (res.ok) {
        alert('Transactions saved successfully to local SQLite!');
        loadStoredTransactions();
      } else {
        alert('Failed to save table.');
      }
    } catch (e) {
      alert(`Error saving: ${e.message}`);
    }
  });

  document.getElementById('downloadCsvBtn').addEventListener('click', () => {
    window.location.href = '/api/backend/export/csv';
  });

  document.getElementById('downloadXlsxBtn').addEventListener('click', () => {
    window.location.href = '/api/backend/export/xlsx';
  });

  document.getElementById('clearAllBtn').addEventListener('click', async () => {
    if (confirm('Clear all local transactions and anomalies from SQLite?')) {
      await fetch('/api/backend/transactions', { method: 'DELETE' });
      currentTransactions = [];
      renderTransactionsTable([]);
      loadStoredTransactions();
    }
  });
}

// 8. Weekly Summary Card
function renderSummaryCard(summary) {
  const sec = document.getElementById('summarySection');
  sec.classList.remove('hidden');

  document.getElementById('summaryPeriod').textContent = summary.period || 'Recent Period';
  document.getElementById('summaryText').textContent = summary.plain_language_summary || '';
  document.getElementById('summarySales').textContent = `₹${(summary.total_sales || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  document.getElementById('summaryExpenses').textContent = `₹${(summary.total_expenses || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  
  const net = summary.net_cash_flow || 0;
  const netEl = document.getElementById('summaryNet');
  netEl.textContent = `₹${net.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  netEl.className = net >= 0 ? 'stat-val text-green' : 'stat-val text-red';
}

// 9. Anomalies Display
function renderAnomalies(anomalyResponse) {
  const sec = document.getElementById('anomaliesSection');
  const countEl = document.getElementById('anomalyCount');
  const listEl = document.getElementById('anomaliesList');
  listEl.innerHTML = '';

  const anomalies = anomalyResponse.anomalies || [];
  countEl.textContent = anomalies.length;

  if (anomalies.length === 0) {
    sec.classList.add('hidden');
    return;
  }

  sec.classList.remove('hidden');
  anomalies.forEach(a => {
    const card = document.createElement('div');
    card.className = 'anomaly-card';
    card.innerHTML = `
      <div class="anomaly-desc">
        <strong>${escapeHtml(a.party)}</strong>: ${escapeHtml(a.reason)}
      </div>
      <div class="anomaly-meta">
        ${a.date} | Rs ${(a.amount || 0).toLocaleString('en-IN')} | Score: ${(a.score || 0).toFixed(2)}
      </div>
    `;
    listEl.appendChild(card);
  });
}

// 10. Forecast Chart (Chart.js)
function setupForecastActions() {
  document.getElementById('seedDemoBtn').addEventListener('click', async () => {
    const btn = document.getElementById('seedDemoBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Seeding 35 Days...';
    try {
      const res = await fetch('/api/backend/seed-demo?days=35', { method: 'POST' });
      if (res.ok) {
        await loadStoredTransactions();
      }
    } catch (e) {
      alert(`Seeding failed: ${e.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = '🎲 Load 35-Day Demo History';
    }
  });

  document.getElementById('refreshForecastBtn').addEventListener('click', async () => {
    try {
      const res = await fetch('/api/backend/forecast?days=30', { method: 'POST' });
      if (res.ok) {
        renderForecastChart(await res.json());
      }
    } catch (e) {
      alert(`Forecast failed: ${e.message}`);
    }
  });
}

function renderForecastChart(forecastData) {
  const banner = document.getElementById('insufficientBanner');
  const chartWrapper = document.getElementById('chartWrapper');

  if (forecastData.status === 'insufficient_data') {
    banner.classList.remove('hidden');
    document.getElementById('insufficientMsg').textContent = forecastData.message;
    chartWrapper.classList.add('hidden');
    return;
  }

  banner.classList.add('hidden');
  chartWrapper.classList.remove('hidden');

  const points = forecastData.forecast_points || [];
  const labels = points.map(p => p.date);
  const projected = points.map(p => p.predicted_net_cash_flow);
  const upper = points.map(p => p.upper_bound);
  const lower = points.map(p => p.lower_bound);

  const ctx = document.getElementById('forecastChart').getContext('2d');
  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  forecastChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Upper Bound (95%)',
          data: upper,
          borderColor: 'transparent',
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          fill: '+1',
          pointRadius: 0,
        },
        {
          label: 'Lower Bound (95%)',
          data: lower,
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
        },
        {
          label: 'Predicted Daily Net Cash Flow (₹)',
          data: projected,
          borderColor: '#2563eb',
          backgroundColor: '#2563eb',
          borderWidth: 2.5,
          tension: 0.25,
          pointRadius: 3,
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            filter: item => item.text.includes('Predicted') || item.text.includes('Upper Bound')
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              return `${context.dataset.label}: ₹${val.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Date (Next 30 Days)' },
          grid: { color: '#f1f5f9' }
        },
        y: {
          title: { display: true, text: 'Net Cash Flow (INR)' },
          grid: { color: '#e2e8f0' }
        }
      }
    }
  });
}
