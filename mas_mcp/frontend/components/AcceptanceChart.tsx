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

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Filler);

interface Cycle {
  id: string;
  accepted: number;
  generated: number;
}

interface AcceptanceChartProps {
  cycles: Cycle[];
}

export default function AcceptanceChart({ cycles }: AcceptanceChartProps) {
  const labels = cycles.map((c) => c.id.split('_')[1] || c.id);
  const rates = cycles.map((c) => 
    c.generated > 0 ? ((c.accepted / c.generated) * 100) : 0
  );

  const data = {
    labels,
    datasets: [
      {
        label: 'Acceptance Rate (%)',
        data: rates,
        borderColor: 'rgb(34, 197, 94)', // Tailwind green-500
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: 'rgb(34, 197, 94)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
      {
        label: 'SLO Threshold (35%)',
        data: Array(cycles.length).fill(35),
        borderColor: 'rgba(239, 68, 68, 0.5)', // Tailwind red-500
        borderDash: [5, 5],
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
        position: 'top' as const,
        labels: {
          color: '#9ca3af', // gray-400
        },
      },
      tooltip: {
        backgroundColor: '#1a1a2e',
        titleColor: '#f3f4f6',
        bodyColor: '#d1d5db',
        borderColor: '#374151',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
        ticks: {
          color: '#9ca3af',
        },
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
        ticks: {
          color: '#9ca3af',
          callback: (value: number | string) => `${value}%`,
        },
      },
    },
  };

  return (
    <div className="card p-4">
      <h3 className="text-lg font-bold mb-4 text-gray-100">Acceptance Rate Trend</h3>
      <div className="h-64">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
