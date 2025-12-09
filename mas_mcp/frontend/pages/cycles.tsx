import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import with SSR disabled
const CycleTable = dynamic(() => import('../components/CycleTable'), { ssr: false });

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
}

export default function CyclesPage() {
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20;

  const fetchCycles = async (pageNum: number) => {
    try {
      const offset = (pageNum - 1) * limit;
      const res = await fetch(`/api/cycles?limit=${limit}&offset=${offset}`);
      if (!res.ok) throw new Error('Failed to fetch cycles');
      const data = await res.json() as { data?: Cycle[]; has_more?: boolean } | Cycle[];
      const cyclesData = Array.isArray(data) ? data : (data.data || []);
      const hasMoreData = Array.isArray(data) ? data.length === limit : (data.has_more ?? false);
      setCycles(cyclesData);
      setHasMore(hasMoreData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCycles(page);
  }, [page]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-xl">Loading cycles...</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">📊 Cycle History</h1>
          <p className="text-gray-500 mt-1">All genesis cycles with metrics</p>
        </div>
        <a href="/" className="text-mas-highlight hover:underline">
          ← Back to Dashboard
        </a>
      </div>

      <CycleTable cycles={cycles} />

      {/* Pagination */}
      <div className="flex items-center justify-center gap-4 mt-6">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 bg-mas-accent text-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-mas-highlight transition-colors"
        >
          Previous
        </button>
        <span className="text-gray-400">Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={!hasMore}
          className="px-4 py-2 bg-mas-accent text-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-mas-highlight transition-colors"
        >
          Next
        </button>
      </div>
    </main>
  );
}
