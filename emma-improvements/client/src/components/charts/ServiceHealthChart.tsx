import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { useDashboardStats } from '@/hooks/useServices';

const COLORS = {
  healthy: '#22c55e',
  degraded: '#eab308',
  unhealthy: '#ef4444',
};

export function ServiceHealthChart() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading || !stats) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Lade Daten...</div>
      </div>
    );
  }

  const data = [
    { name: 'Healthy', value: stats.healthy_count, color: COLORS.healthy },
    { name: 'Degraded', value: stats.degraded_count, color: COLORS.degraded },
    { name: 'Unhealthy', value: stats.unhealthy_count, color: COLORS.unhealthy },
  ].filter(d => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <p className="text-gray-500">Keine Services konfiguriert</p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Service Health</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={2} dataKey="value">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
            <Legend verticalAlign="bottom" height={36} formatter={(value) => <span className="text-gray-300 text-sm">{value}</span>} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 text-center">
        <p className="text-3xl font-bold text-white">{stats.total_services}</p>
        <p className="text-sm text-gray-400">Services gesamt</p>
      </div>
    </div>
  );
}
