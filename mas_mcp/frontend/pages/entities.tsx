import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import EntityCard with no SSR to prevent pre-render issues
const EntityCard = dynamic(() => import('../components/EntityCard'), { ssr: false });

interface Entity {
  name: string;
  tier?: number;
  whr?: number;
  cup?: string;
  faction?: string;
  status?: 'validated' | 'pending' | 'error';
}

// Force SSR to prevent static generation issues
export async function getServerSideProps() {
  return { props: {} };
}

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    const fetchEntities = async () => {
      try {
        const res = await fetch('/api/entities');
        if (!res.ok) throw new Error('Failed to fetch entities');
        const data = await res.json() as Entity[] | { data?: Entity[] };
        // Handle both array and object response formats
        let entityList: Entity[];
        if (Array.isArray(data)) {
          entityList = data;
        } else if (data.data) {
          entityList = data.data;
        } else {
          entityList = [];
        }
        setEntities(entityList);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchEntities();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-xl">Loading entities...</div>
      </div>
    );
  }

  const filteredEntities = filter === 'all' 
    ? entities 
    : entities.filter(e => e.tier?.toString() === filter || e.status === filter);

  const tiers = [...new Set(entities.map(e => e.tier).filter(t => t !== undefined))].sort();

  return (
    <main className="min-h-screen p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">👥 Entity Registry</h1>
          <p className="text-gray-500 mt-1">{entities.length} entities registered</p>
        </div>
        <a href="/" className="text-mas-highlight hover:underline">
          ← Back to Dashboard
        </a>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded text-sm ${filter === 'all' ? 'bg-mas-highlight text-white' : 'bg-mas-accent text-gray-300'}`}
        >
          All
        </button>
        {tiers.map(tier => (
          <button
            key={tier}
            onClick={() => setFilter(tier?.toString() || '')}
            className={`px-3 py-1 rounded text-sm ${filter === tier?.toString() ? 'bg-mas-highlight text-white' : 'bg-mas-accent text-gray-300'}`}
          >
            Tier {tier}
          </button>
        ))}
        <button
          onClick={() => setFilter('validated')}
          className={`px-3 py-1 rounded text-sm ${filter === 'validated' ? 'bg-mas-success text-white' : 'bg-mas-accent text-gray-300'}`}
        >
          Validated
        </button>
        <button
          onClick={() => setFilter('pending')}
          className={`px-3 py-1 rounded text-sm ${filter === 'pending' ? 'bg-mas-warning text-white' : 'bg-mas-accent text-gray-300'}`}
        >
          Pending
        </button>
      </div>

      {/* Entity Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.map((entity, idx) => (
          <EntityCard key={entity.name || idx} entity={entity} />
        ))}
      </div>

      {filteredEntities.length === 0 && (
        <div className="text-center text-gray-500 py-12">
          No entities found matching the filter.
        </div>
      )}
    </main>
  );
}
