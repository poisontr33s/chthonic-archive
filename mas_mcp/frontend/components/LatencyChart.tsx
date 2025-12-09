'use client';

import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

interface LatencyData {
  latency_p50?: number;
  latency_p95?: number;
  latency_p99?: number;
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
}

interface LatencyChartProps {
  digest: LatencyData;
}

export default function LatencyChart({ digest }: LatencyChartProps) {
  // Handle both naming conventions
  const p50 = digest.latency_p50 ?? digest.p50_latency_ms ?? 0;
  const p95 = digest.latency_p95 ?? digest.p95_latency_ms ?? 0;
  const p99 = digest.latency_p99 ?? digest.p99_latency_ms ?? 0;

  const data = {
    labels: ['P50', 'P95', 'P99'],
    datasets: [
      {
        label: 'Latency (ms)',
        data: [p50, p95, p99],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',  // blue-500
          'rgba(245, 158, 11, 0.8)',  // amber-500
          'rgba(239, 68, 68, 0.8)',   // red-500
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2,
        borderRadius: 4,
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
        backgroundColor: '#1a1a2e',
        titleColor: '#f3f4f6',
        bodyColor: '#d1d5db',
        borderColor: '#374151',
        borderWidth: 1,
        callbacks: {
          label: (context: any) => `${context.parsed.y.toFixed(2)} ms`,
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#9ca3af',
          font: {
            weight: 'bold' as const,
          },
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
        ticks: {
          color: '#9ca3af',
          callback: (value: number | string) => `${value} ms`,
        },
      },
    },
  };

  return (
    <div className="card p-4">
      <h3 className="text-lg font-bold mb-4 text-gray-100">Latency Distribution</h3>
      <div className="h-64">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
