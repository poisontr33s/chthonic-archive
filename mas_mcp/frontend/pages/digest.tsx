import { useEffect, useState, type ChangeEvent } from 'react';
import dynamic from 'next/dynamic';

// Dynamic imports with SSR disabled for chart components
const StatCard = dynamic(() => import('../components/StatCard'), { ssr: false });
const AcceptanceChart = dynamic(() => import('../components/AcceptanceChart'), { ssr: false });
const LatencyChart = dynamic(() => import('../components/LatencyChart'), { ssr: false });
const CycleTable = dynamic(() => import('../components/CycleTable'), { ssr: false });
const QualityTrendChart = dynamic(() => import('../components/QualityTrendChart'), { ssr: false });

// Force SSR to prevent static generation issues
export async function getServerSideProps() {
  return { props: {} };
}

interface Cycle {
  id: string;
  accepted: number;
  generated: number;
  providers?: string[];
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  timestamp?: string;
}

interface DailyDigest {
  date: string;
  cycles: Cycle[];
  total_generated: number;
  total_accepted: number;
  avg_acceptance_rate: number;
  avg_p50_latency: number;
  avg_p95_latency: number;
}

interface MonitoringScore {
  timestamp: string;
  acceptance_pct: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  error_count: number;
  quality_score: number;
  slo_compliance: {
    acceptance_rate: boolean;
    p50_latency: boolean;
    p95_latency: boolean;
    vram: boolean;
    overall?: boolean;
  };
  cycle_count?: number;
  window_hours?: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🎯 Governance Thresholds (aligned with MonitoringCard)
// ═══════════════════════════════════════════════════════════════════════════════
const SLO_THRESHOLD = 35;
const GOVERNANCE_WARNING = 70;
const GOVERNANCE_SUCCESS = 90;

function getGovernanceBadge(score: number): { icon: string; label: string; className: string } {
  if (score >= GOVERNANCE_SUCCESS) {
    return { icon: '✅', label: 'Governance Compliant', className: 'badge-success' };
  } else if (score >= GOVERNANCE_WARNING) {
    return { icon: '⚠️', label: 'Warning Zone', className: 'badge-warning' };
  } else if (score >= SLO_THRESHOLD) {
    return { icon: '📊', label: 'SLO Met', className: 'badge-success' };
  } else {
    return { icon: '🚨', label: 'Below SLO', className: 'badge-error' };
  }
}

export default function DigestPage() {
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringScore | null>(null);
  const [monitoringHistory, setMonitoringHistory] = useState<MonitoringScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch cycles, monitoring score, and history in parallel
        const [cyclesRes, monitoringRes, historyRes] = await Promise.all([
          fetch('/api/cycles?limit=100'),
          fetch('/api/monitoring'),
          fetch('/api/metrics/history'),
        ]);
        
        // Process cycles
        if (!cyclesRes.ok) throw new Error('Failed to fetch cycles');
        const response = await cyclesRes.json() as { data?: Cycle[] } | Cycle[];
        const allCycles: Cycle[] = Array.isArray(response) ? response : (response.data || []);
        
        // Filter cycles by selected date
        const dateCycles = allCycles.filter(c => {
          const cycleDate = c.id.split('_')[0];
          return cycleDate === selectedDate.replace(/-/g, '');
        });

        // Calculate aggregates
        const totalGenerated = dateCycles.reduce((sum, c) => sum + c.generated, 0);
        const totalAccepted = dateCycles.reduce((sum, c) => sum + c.accepted, 0);
        const avgRate = totalGenerated > 0 ? (totalAccepted / totalGenerated) * 100 : 0;
        const avgP50 = dateCycles.length > 0 
          ? dateCycles.reduce((sum, c) => sum + (c.p50_latency_ms || 0), 0) / dateCycles.length 
          : 0;
        const avgP95 = dateCycles.length > 0 
          ? dateCycles.reduce((sum, c) => sum + (c.p95_latency_ms || 0), 0) / dateCycles.length 
          : 0;

        setDigest({
          date: selectedDate,
          cycles: dateCycles,
          total_generated: totalGenerated,
          total_accepted: totalAccepted,
          avg_acceptance_rate: avgRate,
          avg_p50_latency: avgP50,
          avg_p95_latency: avgP95,
        });
        
        // Process monitoring score
        if (monitoringRes.ok) {
          const monitoringData = await monitoringRes.json() as MonitoringScore;
          setMonitoring(monitoringData);
        }
        
        // Process monitoring history for trend chart
        if (historyRes.ok) {
          const historyData = await historyRes.json() as { data?: MonitoringScore[] };
          if (historyData.data && Array.isArray(historyData.data)) {
            setMonitoringHistory(historyData.data);
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedDate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-xl">Loading digest...</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">📅 Daily Digest</h1>
          <p className="text-gray-500 mt-1">Aggregated cycle reports by date</p>
        </div>
        <div className="flex items-center gap-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e: ChangeEvent<HTMLInputElement>) => {
              setSelectedDate(e.target.value);
            }}
            className="bg-mas-dark border border-gray-700 rounded px-3 py-2 text-gray-100"
          />
          <a href="/" className="text-mas-highlight hover:underline">
            ← Dashboard
          </a>
        </div>
      </div>

      {digest && digest.cycles.length > 0 ? (
        <>
          {/* Monitoring Score Artifact Viewer */}
          {monitoring && (
            <div className="card p-6 mb-8">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                    🎯 Monitoring Score Artifact
                  </h2>
                  <p className="text-gray-500 text-sm mt-1">
                    From monitoring_score.json • Last {monitoring.window_hours || 24}h window
                  </p>
                </div>
                <div className="text-right">
                  {(() => {
                    const badge = getGovernanceBadge(monitoring.quality_score);
                    return (
                      <span className={`${badge.className} flex items-center gap-1`}>
                        <span>{badge.icon}</span>
                        <span>{badge.label}</span>
                      </span>
                    );
                  })()}
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Quality Score</p>
                  <p className={`text-2xl font-bold ${
                    monitoring.quality_score >= GOVERNANCE_SUCCESS ? 'text-green-400' :
                    monitoring.quality_score >= GOVERNANCE_WARNING ? 'text-yellow-400' :
                    monitoring.quality_score >= SLO_THRESHOLD ? 'text-green-400' :
                    'text-red-400'
                  }`}>
                    {monitoring.quality_score.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Acceptance %</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {monitoring.acceptance_pct.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">P50 Latency</p>
                  <p className={`text-2xl font-bold ${monitoring.slo_compliance.p50_latency ? 'text-green-400' : 'text-red-400'}`}>
                    {monitoring.latency_p50_ms.toFixed(2)}ms
                  </p>
                </div>
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">P95 Latency</p>
                  <p className={`text-2xl font-bold ${monitoring.slo_compliance.p95_latency ? 'text-green-400' : 'text-red-400'}`}>
                    {monitoring.latency_p95_ms.toFixed(2)}ms
                  </p>
                </div>
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Errors</p>
                  <p className={`text-2xl font-bold ${monitoring.error_count === 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {monitoring.error_count}
                  </p>
                </div>
                <div className="bg-mas-dark/50 rounded-lg p-3 border border-gray-800">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Timestamp</p>
                  <p className="text-sm font-mono text-gray-300">
                    {new Date(monitoring.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
              
              {/* SLO Compliance Grid */}
              <div className="mt-4 pt-4 border-t border-gray-800">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">SLO Compliance</p>
                <div className="flex flex-wrap gap-2">
                  <span className={`badge ${monitoring.slo_compliance.acceptance_rate ? 'badge-success' : 'badge-error'}`}>
                    {monitoring.slo_compliance.acceptance_rate ? '✓' : '✗'} Acceptance Rate
                  </span>
                  <span className={`badge ${monitoring.slo_compliance.p50_latency ? 'badge-success' : 'badge-error'}`}>
                    {monitoring.slo_compliance.p50_latency ? '✓' : '✗'} P50 Latency
                  </span>
                  <span className={`badge ${monitoring.slo_compliance.p95_latency ? 'badge-success' : 'badge-error'}`}>
                    {monitoring.slo_compliance.p95_latency ? '✓' : '✗'} P95 Latency
                  </span>
                  <span className={`badge ${monitoring.slo_compliance.vram ? 'badge-success' : 'badge-error'}`}>
                    {monitoring.slo_compliance.vram ? '✓' : '✗'} VRAM
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            <StatCard
              title="Cycles Today"
              value={digest.cycles.length}
              status="neutral"
            />
            <StatCard
              title="Generated"
              value={digest.total_generated}
              status="neutral"
            />
            <StatCard
              title="Accepted"
              value={digest.total_accepted}
              status="success"
            />
            <StatCard
              title="Avg Rate"
              value={`${digest.avg_acceptance_rate.toFixed(1)}%`}
              status={digest.avg_acceptance_rate >= 35 ? 'success' : 'warning'}
            />
            <StatCard
              title="Avg P50"
              value={`${digest.avg_p50_latency.toFixed(2)}ms`}
              status={digest.avg_p50_latency < 2 ? 'success' : 'warning'}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <AcceptanceChart cycles={digest.cycles} />
            <LatencyChart 
              digest={{
                p50_latency_ms: digest.avg_p50_latency,
                p95_latency_ms: digest.avg_p95_latency,
                p99_latency_ms: digest.avg_p95_latency * 1.2, // estimate
              }} 
            />
          </div>

          {/* Historical Quality Score Trend */}
          {monitoringHistory.length > 0 && (
            <div className="mb-8">
              <QualityTrendChart 
                scores={monitoringHistory} 
                title="Historical Quality Score Trend"
                showLatency={true}
              />
            </div>
          )}

          {/* Cycles Table */}
          <div>
            <h2 className="text-xl font-bold text-gray-100 mb-4">
              Cycles on {new Date(selectedDate).toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h2>
            <CycleTable cycles={digest.cycles} />
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500 text-xl">No cycles found for {selectedDate}</p>
          <p className="text-gray-600 mt-2">Try selecting a different date.</p>
        </div>
      )}
    </main>
  );
}
