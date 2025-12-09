'use client';

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

/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * 🎯 MonitoringCard - Quality Score Trend Visualization
 * ─────────────────────────────────────────────────────────────────────────────────
 * Displays quality score (acceptance rate) drift over the last 7 days with:
 * - Current score prominently displayed
 * - Trend line with gradient fill
 * - SLO threshold indicator
 * - Score change indicator (↑/↓)
 * ═══════════════════════════════════════════════════════════════════════════════
 */

interface DayDigest {
  date: string;
  total_cycles: number;
  total_generated: number;
  total_accepted: number;
  acceptance_rate?: number;
}

interface MetricsData {
  current_date: string;
  days: DayDigest[];
  totals: {
    cycles: number;
    generated: number;
    accepted: number;
  };
}

interface MonitoringCardProps {
  metrics: MetricsData | null;
  isLoading?: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 Governance Thresholds
// ─────────────────────────────────────────────────────────────────────────────────
// SLO_THRESHOLD:     Minimum acceptable quality (35%)
// GOVERNANCE_WARNING: Warning zone boundary (70%)  → ⚠️ badge
// GOVERNANCE_SUCCESS: Governance compliant (90%)   → ✅ badge
// ═══════════════════════════════════════════════════════════════════════════════
const SLO_THRESHOLD = 35;        // Minimum SLO (35% acceptance rate)
const GOVERNANCE_WARNING = 70;   // Below this = ⚠️ warning
const GOVERNANCE_SUCCESS = 90;   // At or above = ✅ governance compliant

export default function MonitoringCard({ metrics, isLoading }: MonitoringCardProps) {
  if (isLoading) {
    return (
      <div className="card p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-48 mb-4"></div>
        <div className="h-32 bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (!metrics || metrics.days.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-100 mb-4">
          📊 Quality Score Trend
        </h3>
        <div className="text-gray-500 text-center py-8">
          No metrics data available
        </div>
      </div>
    );
  }

  // Calculate acceptance rates for each day (reversed for chronological order)
  const sortedDays = [...metrics.days].sort((a, b) => a.date.localeCompare(b.date));
  
  const scores = sortedDays.map((day) => 
    day.total_generated > 0 
      ? ((day.total_accepted / day.total_generated) * 100)
      : 0
  );

  // Current and previous scores for trend indicator
  const currentScore = scores.length > 0 ? scores[scores.length - 1] : 0;
  const previousScore = scores.length > 1 ? scores[scores.length - 2] : currentScore;
  const scoreDelta = currentScore - previousScore;
  
  // Average score for context
  const avgScore = scores.length > 0 
    ? scores.reduce((a, b) => a + b, 0) / scores.length 
    : 0;

  // Governance status based on multi-tier thresholds
  const getGovernanceStatus = (score: number): { 
    icon: string; 
    label: string; 
    className: string;
    color: string;
    bgColor: string;
  } => {
    if (score >= GOVERNANCE_SUCCESS) {
      return {
        icon: '✅',
        label: 'Governance Compliant',
        className: 'badge-success',
        color: 'rgb(34, 197, 94)',
        bgColor: 'rgba(34, 197, 94, 0.1)',
      };
    } else if (score >= GOVERNANCE_WARNING) {
      return {
        icon: '⚠️',
        label: 'Warning Zone',
        className: 'badge-warning',
        color: 'rgb(251, 191, 36)',
        bgColor: 'rgba(251, 191, 36, 0.1)',
      };
    } else if (score >= SLO_THRESHOLD) {
      return {
        icon: '📊',
        label: 'SLO Met',
        className: 'badge-success',
        color: 'rgb(34, 197, 94)',
        bgColor: 'rgba(34, 197, 94, 0.1)',
      };
    } else {
      return {
        icon: '🚨',
        label: 'Below SLO',
        className: 'badge-error',
        color: 'rgb(239, 68, 68)',
        bgColor: 'rgba(239, 68, 68, 0.1)',
      };
    }
  };

  const governance = getGovernanceStatus(currentScore);

  // Status based on SLO
  const isAboveSLO = currentScore >= SLO_THRESHOLD;
  const statusColor = governance.color;
  const statusBg = governance.bgColor;

  // Format dates for display
  const labels = sortedDays.map((day) => {
    const d = new Date(day.date);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Quality Score (%)',
        data: scores,
        borderColor: statusColor,
        backgroundColor: statusBg,
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 8,
        pointBackgroundColor: statusColor,
        pointBorderColor: '#1a1a2e',
        pointBorderWidth: 2,
      },
      {
        label: '✅ Governance (90%)',
        data: Array(scores.length).fill(GOVERNANCE_SUCCESS),
        borderColor: 'rgba(34, 197, 94, 0.5)',
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
      },
      {
        label: '⚠️ Warning (70%)',
        data: Array(scores.length).fill(GOVERNANCE_WARNING),
        borderColor: 'rgba(251, 191, 36, 0.5)',
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
      },
      {
        label: 'SLO Threshold (35%)',
        data: Array(scores.length).fill(SLO_THRESHOLD),
        borderColor: 'rgba(239, 68, 68, 0.6)',
        borderDash: [6, 4],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
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
            return `${context.dataset.label || 'Score'}: ${value.toFixed(1)}%`;
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
          font: { size: 11 },
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
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  // Trend indicator
  const trendIcon = scoreDelta > 0 ? '↑' : scoreDelta < 0 ? '↓' : '→';
  const trendColor = scoreDelta > 0 ? 'text-green-400' : scoreDelta < 0 ? 'text-red-400' : 'text-gray-400';

  return (
    <div className="card p-6">
      {/* Header with current score */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">
            📊 Quality Score Trend
          </h3>
          <p className="text-gray-500 text-sm mt-1">
            Last {metrics.days.length} days • SLO: {SLO_THRESHOLD}%
          </p>
        </div>
        
        {/* Current Score Badge */}
        <div className="text-right">
          <div className="flex items-center gap-2">
            <span className={`text-3xl font-bold`} style={{ color: governance.color }}>
              {currentScore.toFixed(1)}%
            </span>
            <span className={`text-lg ${trendColor}`} title={`${scoreDelta >= 0 ? '+' : ''}${scoreDelta.toFixed(1)}% from previous`}>
              {trendIcon}
            </span>
          </div>
          <span className={`text-xs ${governance.className} flex items-center gap-1`}>
            <span>{governance.icon}</span>
            <span>{governance.label}</span>
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-48">
        <Line data={data} options={options} />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-700">
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">7-Day Avg</p>
          <p className="text-lg font-semibold text-gray-200">{avgScore.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Total Cycles</p>
          <p className="text-lg font-semibold text-gray-200">{metrics.totals.cycles}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Accepted</p>
          <p className="text-lg font-semibold text-green-400">{metrics.totals.accepted}</p>
        </div>
      </div>
    </div>
  );
}
