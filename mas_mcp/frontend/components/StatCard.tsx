interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  status?: 'success' | 'warning' | 'error' | 'neutral';
  icon?: React.ReactNode;
}

export default function StatCard({ title, value, subtitle, status = 'neutral', icon }: StatCardProps) {
  const statusColors = {
    success: 'text-mas-success',
    warning: 'text-mas-warning',
    error: 'text-mas-error',
    neutral: 'text-gray-100',
  };

  const statusBg = {
    success: 'bg-mas-success/10',
    warning: 'bg-mas-warning/10',
    error: 'bg-mas-error/10',
    neutral: 'bg-mas-accent/20',
  };

  return (
    <div className={`card p-4 ${statusBg[status]}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">{title}</h3>
        {icon && <div className="text-gray-500">{icon}</div>}
      </div>
      <p className={`mt-2 text-3xl font-bold ${statusColors[status]}`}>{value}</p>
      {subtitle && (
        <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
      )}
    </div>
  );
}
