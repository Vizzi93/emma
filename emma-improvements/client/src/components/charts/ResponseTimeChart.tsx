import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useServices } from '@/hooks/useServices';

export function ResponseTimeChart() {
  const { data: servicesData, isLoading } = useServices();

  if (isLoading) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Lade Daten...</div>
      </div>
    );
  }

  const services = servicesData?.items || [];
  const activeServices = services.filter(s => s.is_active && s.last_response_time_ms);

  if (activeServices.length === 0) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <p className="text-gray-500">Keine Response-Daten verfügbar</p>
      </div>
    );
  }

  // Group by response time ranges for visualization
  const data = activeServices.slice(0, 10).map(service => ({
    name: service.name.length > 15 ? service.name.slice(0, 15) + '...' : service.name,
    responseTime: service.last_response_time_ms || 0,
    uptime: service.uptime_percentage || 0,
  }));

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Response Times</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} angle={-20} textAnchor="end" height={50} />
            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} unit="ms" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: number) => [`${value}ms`, 'Response']}
            />
            <Line type="monotone" dataKey="responseTime" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
