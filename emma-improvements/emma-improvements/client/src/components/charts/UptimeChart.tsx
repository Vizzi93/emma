import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useServices } from '@/hooks/useServices';

const getUptimeColor = (uptime: number) => {
  if (uptime >= 99.9) return '#22c55e';
  if (uptime >= 99) return '#84cc16';
  if (uptime >= 95) return '#eab308';
  if (uptime >= 90) return '#f97316';
  return '#ef4444';
};

export function UptimeChart() {
  const { data: servicesData, isLoading } = useServices();

  if (isLoading) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Lade Daten...</div>
      </div>
    );
  }

  const services = servicesData?.items || [];
  const activeServices = services.filter(s => s.is_active);

  if (activeServices.length === 0) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <p className="text-gray-500">Keine Uptime-Daten verfügbar</p>
      </div>
    );
  }

  const data = activeServices.slice(0, 8).map(service => ({
    name: service.name.length > 12 ? service.name.slice(0, 12) + '...' : service.name,
    uptime: service.uptime_percentage || 0,
  }));

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Service Uptime (24h)</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} angle={-20} textAnchor="end" height={50} />
            <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Uptime']}
            />
            <Bar dataKey="uptime" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getUptimeColor(entry.uptime)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
