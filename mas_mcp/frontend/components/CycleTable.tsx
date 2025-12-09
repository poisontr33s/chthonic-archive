interface Cycle {
  id: string;
  accepted: number;
  generated: number;
  providers?: string[];
  p50_latency_ms?: number;
  p95_latency_ms?: number;
}

interface CycleTableProps {
  cycles: Cycle[];
}

export default function CycleTable({ cycles }: CycleTableProps) {
  const getStatusBadge = (rate: number) => {
    if (rate >= 35) return 'badge-success';
    if (rate >= 20) return 'badge-warning';
    return 'badge-error';
  };

  return (
    <div className="card overflow-hidden">
      <table className="min-w-full">
        <thead className="bg-mas-accent/30">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Cycle ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Accepted
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Rate
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              P50 / P95
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
              Providers
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700/50">
          {cycles.map((cycle) => {
            const rate = cycle.generated > 0 
              ? ((cycle.accepted / cycle.generated) * 100).toFixed(1) 
              : '0.0';
            
            return (
              <tr key={cycle.id} className="hover:bg-mas-accent/10 transition-colors">
                <td className="px-4 py-3 text-sm font-mono text-gray-300">
                  {cycle.id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300">
                  {cycle.accepted} / {cycle.generated}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={getStatusBadge(parseFloat(rate))}>
                    {rate}%
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">
                  {cycle.p50_latency_ms?.toFixed(2) ?? '0.00'}ms / {cycle.p95_latency_ms?.toFixed(2) ?? '0.00'}ms
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">
                  {cycle.providers?.join(', ') || 'N/A'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
