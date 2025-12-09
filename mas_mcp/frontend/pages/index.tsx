import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamic imports with SSR disabled for chart components
const StatCard = dynamic(() => import('../components/StatCard'), { ssr: false });
const AcceptanceChart = dynamic(() => import('../components/AcceptanceChart'), { ssr: false });
const LatencyChart = dynamic(() => import('../components/LatencyChart'), { ssr: false });
const CycleTable = dynamic(() => import('../components/CycleTable'), { ssr: false });
const MonitoringCard = dynamic(() => import('../components/MonitoringCard'), { ssr: false });

// Force SSR to prevent static generation issues
export async function getServerSideProps() {
  return { props: {} };
}

interface Digest {
  total_cycles: number;
  generated: number;
  accepted: number;
  acceptance_rate?: number;
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
}

interface Cycle {
  id: string;
  accepted: number;
  generated: number;
  providers?: string[];
  p50_latency_ms?: number;
  p95_latency_ms?: number;
}

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

export default function Dashboard() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      const [digestRes, cyclesRes, metricsRes] = await Promise.all([
        fetch('/api/digest'),
        fetch('/api/cycles?limit=10'),
        fetch('/api/metrics'),
      ]);

      if (!digestRes.ok || !cyclesRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const digestData = await digestRes.json() as Digest;
      const cyclesData = await cyclesRes.json() as { data?: Cycle[] } | Cycle[];

      setDigest(digestData);
      setCycles(Array.isArray(cyclesData) ? cyclesData : (cyclesData.data || []));
      setLastUpdated(new Date());
      setError(null);

      // Handle metrics separately (may not be available)
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json() as MetricsData;
        setMetrics(metricsData);
      }
      setMetricsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setMetricsLoading(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // 30s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-xl">Loading MAS-MCP Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-mas-error text-xl">Error: {error}</div>
      </div>
    );
  }

  if (!digest) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-xl">No data available</div>
      </div>
    );
  }

  const acceptanceRate = digest.generated > 0 
    ? ((digest.accepted / digest.generated) * 100).toFixed(1)
    : '0.0';
  const rateStatus = parseFloat(acceptanceRate) >= 35 ? 'success' : parseFloat(acceptanceRate) >= 20 ? 'warning' : 'error';

  return (
    <main className="min-h-screen p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">
            🏛️ MAS-MCP Genesis Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            GPU: CUDA+TensorRT | Bun: v1.3.4
          </p>
        </div>
        <div className="text-right">
          <span className="badge-success">● Connected</span>
          {lastUpdated && (
            <p className="text-gray-500 text-sm mt-1">
              Updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Cycles"
          value={digest.total_cycles}
          status="neutral"
        />
        <StatCard
          title="Generated"
          value={digest.generated}
          status="neutral"
        />
        <StatCard
          title="Accepted"
          value={digest.accepted}
          status="success"
        />
        <StatCard
          title="Acceptance Rate"
          value={`${acceptanceRate}%`}
          subtitle={parseFloat(acceptanceRate) >= 35 ? 'SLO Met' : 'Below SLO (35%)'}
          status={rateStatus}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <AcceptanceChart cycles={cycles} />
        <LatencyChart digest={digest} />
      </div>

      {/* Monitoring Card - Quality Score Trend */}
      <div className="mb-8">
        <MonitoringCard metrics={metrics} isLoading={metricsLoading} />
      </div>

      {/* Recent Cycles Table */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-gray-100 mb-4">Recent Cycles</h2>
        <CycleTable cycles={cycles} />
      </div>

      {/* Footer */}
      <footer className="text-center text-gray-600 text-sm py-4 border-t border-gray-800">
        MAS-MCP Genesis Dashboard • Bun-Native Runtime • No Node Fallback
      </footer>
    </main>
  );
}
