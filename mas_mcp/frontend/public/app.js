/**
 * 🧬 MAS-MCP Genesis Dashboard - Client JavaScript
 * Vanilla JS for maximum compatibility (no framework)
 */

// State
let state = {
  health: null,
  digest: null,
  cycles: [],
  refreshInterval: 30000, // 30 seconds
};

// DOM Elements
const elements = {
  status: document.getElementById('status'),
  gpuProvider: document.getElementById('gpu-provider'),
  bunVersion: document.getElementById('bun-version'),
  lastUpdate: document.getElementById('last-update'),
  sloGrid: document.getElementById('slo-grid'),
  totalCycles: document.getElementById('total-cycles'),
  totalGenerated: document.getElementById('total-generated'),
  totalAccepted: document.getElementById('total-accepted'),
  acceptanceRate: document.getElementById('acceptance-rate'),
  degradedCycles: document.getElementById('degraded-cycles'),
  errorCycles: document.getElementById('error-cycles'),
  cyclesList: document.getElementById('cycles-list'),
  latencyChart: document.getElementById('latency-chart'),
};

// API Helpers
async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`[API] Failed to fetch ${url}:`, err);
    return null;
  }
}

// Update health status
async function updateHealth() {
  const health = await fetchJSON('/api/health');
  
  if (health) {
    state.health = health;
    elements.status.textContent = health.status === 'ok' ? '✓ Connected' : '⚠ Degraded';
    elements.status.className = `status ${health.status}`;
    elements.gpuProvider.textContent = `GPU: ${health.gpu_provider}`;
    elements.bunVersion.textContent = `Bun: v${health.bun_version}`;
    elements.lastUpdate.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
  } else {
    elements.status.textContent = '✗ Disconnected';
    elements.status.className = 'status error';
  }
}

// Update digest
async function updateDigest() {
  const digest = await fetchJSON('/api/digest');
  
  if (digest) {
    state.digest = digest;
    
    // Update stats
    elements.totalCycles.textContent = digest.total_cycles;
    elements.totalGenerated.textContent = digest.total_generated;
    elements.totalAccepted.textContent = digest.total_accepted;
    elements.acceptanceRate.textContent = `${(digest.acceptance_rate * 100).toFixed(1)}%`;
    elements.degradedCycles.textContent = digest.degraded_cycles;
    elements.errorCycles.textContent = digest.error_cycles;
    
    // Update SLO indicators
    updateSLO('slo-acceptance', 
      `${(digest.acceptance_rate * 100).toFixed(1)}%`,
      digest.slo_compliance.acceptance_rate);
    updateSLO('slo-p50', 
      `${digest.latency.p50.toFixed(1)}ms`,
      digest.slo_compliance.p50_latency);
    updateSLO('slo-p95', 
      `${digest.latency.p95.toFixed(1)}ms`,
      digest.slo_compliance.p95_latency);
    updateSLO('slo-vram', 
      `${digest.vram_max.toFixed(1)}%`,
      digest.slo_compliance.vram);
  }
}

// Update SLO indicator
function updateSLO(id, value, passed) {
  const el = document.getElementById(id);
  if (!el) return;
  
  el.querySelector('.value').textContent = value;
  el.querySelector('.status').textContent = passed ? '✓' : '✗';
  el.className = `slo-item ${passed ? 'pass' : 'fail'}`;
}

// Update cycles list
async function updateCycles() {
  const result = await fetchJSON('/api/cycles?limit=10');
  
  if (result && result.data) {
    state.cycles = result.data;
    
    if (result.data.length === 0) {
      elements.cyclesList.innerHTML = '<p class="loading-text">No cycles found</p>';
      return;
    }
    
    elements.cyclesList.innerHTML = result.data.map(cycle => `
      <div class="cycle-item">
        <div class="cycle-header">
          <span class="cycle-id">${cycle.cycle_id}</span>
          <span class="cycle-status ${getStatusClass(cycle)}">${getStatusText(cycle)}</span>
        </div>
        <div class="cycle-metrics">
          <span>Accepted: ${cycle.accepted}</span>
          <span>Rate: ${(cycle.acceptance_rate * 100).toFixed(1)}%</span>
          <span>P50: ${cycle.latency_p50_ms?.toFixed(1) || '--'}ms</span>
          <span>P95: ${cycle.latency_p95_ms?.toFixed(1) || '--'}ms</span>
        </div>
      </div>
    `).join('');
    
    // Update latency chart
    updateLatencyChart(result.data);
  }
}

// Get cycle status class
function getStatusClass(cycle) {
  if (cycle.error) return 'error';
  if (cycle.degraded_mode) return 'degraded';
  return 'success';
}

// Get cycle status text
function getStatusText(cycle) {
  if (cycle.error) return 'Error';
  if (cycle.degraded_mode) return 'Degraded';
  return 'OK';
}

// Update latency chart (simple bar chart)
function updateLatencyChart(cycles) {
  if (!cycles.length) {
    elements.latencyChart.innerHTML = '<p class="loading-text">No data</p>';
    return;
  }
  
  // Reverse to show oldest first
  const reversed = [...cycles].reverse();
  const maxLatency = Math.max(...reversed.map(c => c.latency_p95_ms || 0), 1);
  
  elements.latencyChart.innerHTML = reversed.map(cycle => {
    const height = ((cycle.latency_p95_ms || 0) / maxLatency) * 100;
    return `<div class="chart-bar" style="height: ${height}%" title="${cycle.cycle_id}: ${cycle.latency_p95_ms?.toFixed(1) || 0}ms P95"></div>`;
  }).join('');
}

// Initial load
async function init() {
  console.log('[Dashboard] Initializing...');
  
  await Promise.all([
    updateHealth(),
    updateDigest(),
    updateCycles(),
  ]);
  
  console.log('[Dashboard] Initial load complete');
  
  // Set up refresh interval
  setInterval(async () => {
    await updateHealth();
    await updateDigest();
    await updateCycles();
  }, state.refreshInterval);
}

// Start
document.addEventListener('DOMContentLoaded', init);
