// ═══════════════════════════════════════════════════════════════════════════════
// 📈 QualityTrendChart - Historical Quality Score Visualization
// ─────────────────────────────────────────────────────────────────────────────────
// Displays quality score drift over time from monitoring_score_*.json artifacts
// Used for long-term trend analysis and governance compliance tracking
// ═══════════════════════════════════════════════════════════════════════════════

import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import type { TooltipItem } from 'chart.js';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Filler);

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 Governance Thresholds
// ═══════════════════════════════════════════════════════════════════════════════
const SLO_THRESHOLD = 35;
const GOVERNANCE_WARNING = 70;
const GOVERNANCE_SUCCESS = 90;

export interface MonitoringScore {
  timestamp: string;
  acceptance_pct: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  error_count: number;
  quality_score: number;
  cycle_count?: number;
  window_hours?: number;
}

interface QualityTrendChartProps {
  scores: MonitoringScore[];
  title?: string;
  showLatency?: boolean;
}

export default function QualityTrendChart({ 
  scores, 
  title = "Quality Score History",
  showLatency = false 
}: QualityTrendChartProps) {
  if (!scores || scores.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          📈 {title}
        </h3>
        <div className="text-gray-500 text-center py-8">
          No historical monitoring data available
        </div>
      </div>
    );
  }

  // Format timestamps for display
  const labels = scores.map((s) => {
    const d = new Date(s.timestamp);
    return d.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
    });
  });

  // Current and previous for trend
  const currentScore = scores.length > 0 ? scores[scores.length - 1].quality_score : 0;
  const previousScore = scores.length > 1 ? scores[scores.length - 2].quality_score : currentScore;
  const scoreDelta = currentScore - previousScore;

  // Determine color based on current score
  const getScoreColor = (score: number) => {
    if (score >= GOVERNANCE_SUCCESS) return 'rgb(34, 197, 94)';
    if (score >= GOVERNANCE_WARNING) return 'rgb(251, 191, 36)';
    if (score >= SLO_THRESHOLD) return 'rgb(59, 130, 246)';
    return 'rgb(239, 68, 68)';
  };

  const primaryColor = getScoreColor(currentScore);

  const datasets = [
    {
      label: 'Quality Score',
      data: scores.map((s) => s.quality_score),
      borderColor: primaryColor,
      backgroundColor: `${primaryColor}20`,
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 7,
      pointBackgroundColor: primaryColor,
      pointBorderColor: '#1a1a2e',
      pointBorderWidth: 2,
    },
    {
      label: '✅ Governance (90%)',
      data: Array(scores.length).fill(GOVERNANCE_SUCCESS),
      borderColor: 'rgba(34, 197, 94, 0.4)',
      borderDash: [4, 4],
      borderWidth: 1,
      pointRadius: 0,
      fill: false,
    },
    {
      label: '⚠️ Warning (70%)',
      data: Array(scores.length).fill(GOVERNANCE_WARNING),
      borderColor: 'rgba(251, 191, 36, 0.4)',
      borderDash: [4, 4],
      borderWidth: 1,
      pointRadius: 0,
      fill: false,
    },
    {
      label: 'SLO Threshold (35%)',
      data: Array(scores.length).fill(SLO_THRESHOLD),
      borderColor: 'rgba(239, 68, 68, 0.5)',
      borderDash: [6, 4],
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
    },
  ];

  // Optionally add latency trend
  if (showLatency) {
    datasets.push({
      label: 'Latency p95 (ms)',
      data: scores.map((s) => s.latency_p95_ms),
      borderColor: 'rgb(168, 85, 247)',
      backgroundColor: 'rgba(168, 85, 247, 0.1)',
      tension: 0.3,
      fill: false,
      pointRadius: 3,
      pointHoverRadius: 5,
      pointBackgroundColor: 'rgb(168, 85, 247)',
      pointBorderColor: '#1a1a2e',
      pointBorderWidth: 1,
      yAxisID: 'y1',
    } as typeof datasets[0] & { yAxisID: string });
  }

  const data = { labels, datasets };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom' as const,
        labels: {
          color: '#9ca3af',
          font: { size: 10 },
          usePointStyle: true,
          padding: 12,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(26, 26, 46, 0.95)',
        titleColor: '#f3f4f6',
        bodyColor: '#d1d5db',
        borderColor: '#4a5568',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: (context: TooltipItem<'line'>) => {
            const value = context.parsed.y ?? 0;
            const label = context.dataset.label || '';
            if (label.includes('Latency')) {
              return `${label}: ${value.toFixed(0)} ms`;
            }
            return `${label}: ${value.toFixed(1)}%`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
        },
        ticks: {
          color: '#9ca3af',
          font: { size: 10 },
          maxRotation: 45,
          minRotation: 0,
        },
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
        },
        ticks: {
          color: '#9ca3af',
          font: { size: 11 },
          callback: (value: string | number) => `${value}%`,
        },
      },
      ...(showLatency ? {
        y1: {
          position: 'right' as const,
          min: 0,
          grid: {
            drawOnChartArea: false,
          },
          ticks: {
            color: 'rgb(168, 85, 247)',
            font: { size: 10 },
            callback: (value: string | number) => `${value}ms`,
          },
        },
      } : {}),
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  // Trend indicator
  const trendIcon = scoreDelta > 0 ? '↑' : scoreDelta < 0 ? '↓' : '→';
  const trendColor = scoreDelta > 0 ? 'text-green-400' : scoreDelta < 0 ? 'text-red-400' : 'text-gray-400';

  // Stats
  const avgScore = scores.reduce((a, b) => a + b.quality_score, 0) / scores.length;
  const minScore = Math.min(...scores.map(s => s.quality_score));
  const maxScore = Math.max(...scores.map(s => s.quality_score));

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">
            📈 {title}
          </h3>
          <p className="text-gray-500 text-sm mt-1">
            {scores.length} data points • SLO: {SLO_THRESHOLD}%
          </p>
        </div>
        
        {/* Current Score */}
        <div className="text-right">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold" style={{ color: primaryColor }}>
              {currentScore.toFixed(1)}%
            </span>
            <span className={`text-lg ${trendColor}`} title={`${scoreDelta >= 0 ? '+' : ''}${scoreDelta.toFixed(1)}%`}>
              {trendIcon}
            </span>
          </div>
          <span className="text-xs text-gray-500">Latest Score</span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-56">
        <Line data={data} options={options} />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-700">
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Average</p>
          <p className="text-lg font-semibold text-gray-200">{avgScore.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Min</p>
          <p className="text-lg font-semibold text-red-400">{minScore.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Max</p>
          <p className="text-lg font-semibold text-green-400">{maxScore.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Data Points</p>
          <p className="text-lg font-semibold text-gray-200">{scores.length}</p>
        </div>
      </div>

      {/* Governance Badge */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        {currentScore < SLO_THRESHOLD && (
          <p className="text-red-500 font-semibold text-sm flex items-center gap-2">
            <span>🚨</span>
            <span>Below SLO Threshold ({SLO_THRESHOLD}%)</span>
          </p>
        )}
        {currentScore >= SLO_THRESHOLD && currentScore < GOVERNANCE_WARNING && (
          <p className="text-blue-400 font-semibold text-sm flex items-center gap-2">
            <span>📊</span>
            <span>SLO Met - Monitor for improvement</span>
          </p>
        )}
        {currentScore >= GOVERNANCE_WARNING && currentScore < GOVERNANCE_SUCCESS && (
          <p className="text-yellow-400 font-semibold text-sm flex items-center gap-2">
            <span>⚠️</span>
            <span>Warning Zone - Approaching compliance</span>
          </p>
        )}
        {currentScore >= GOVERNANCE_SUCCESS && (
          <p className="text-green-400 font-semibold text-sm flex items-center gap-2">
            <span>✅</span>
            <span>Governance Compliant</span>
          </p>
        )}
      </div>
    </div>
  );
}
