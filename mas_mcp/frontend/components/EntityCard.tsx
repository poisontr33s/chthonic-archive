interface Entity {
  name: string;
  tier?: number;
  whr?: number;
  cup?: string;
  faction?: string;
  status?: 'validated' | 'pending' | 'error';
}

interface EntityCardProps {
  entity: Entity;
}

export default function EntityCard({ entity }: EntityCardProps) {
  const statusColors = {
    validated: 'border-mas-success',
    pending: 'border-mas-warning',
    error: 'border-mas-error',
  };

  const tierColors: Record<number, string> = {
    0: 'text-purple-400',
    1: 'text-blue-400',
    2: 'text-green-400',
    3: 'text-yellow-400',
    4: 'text-gray-400',
  };

  return (
    <div className={`card p-4 border-l-4 ${statusColors[entity.status || 'pending']}`}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-bold text-gray-100">{entity.name}</h3>
          {entity.faction && (
            <p className="text-sm text-gray-500">{entity.faction}</p>
          )}
        </div>
        {entity.tier !== undefined && (
          <span className={`text-sm font-bold ${tierColors[entity.tier] || 'text-gray-400'}`}>
            Tier {entity.tier}
          </span>
        )}
      </div>
      
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        {entity.whr !== undefined && (
          <div>
            <span className="text-gray-500">WHR:</span>
            <span className="ml-1 text-gray-300">{entity.whr.toFixed(3)}</span>
          </div>
        )}
        {entity.cup && (
          <div>
            <span className="text-gray-500">Cup:</span>
            <span className="ml-1 text-gray-300">{entity.cup}</span>
          </div>
        )}
      </div>

      {entity.status && (
        <div className="mt-3">
          <span className={`badge-${entity.status === 'validated' ? 'success' : entity.status === 'pending' ? 'warning' : 'error'}`}>
            {entity.status}
          </span>
        </div>
      )}
    </div>
  );
}
