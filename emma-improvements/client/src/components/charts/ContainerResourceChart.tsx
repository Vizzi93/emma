import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useContainers } from '@/hooks/useDocker';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ContainerStats } from '@/types/docker';

export function ContainerResourceChart() {
  const { data: containersData, isLoading: containersLoading } = useContainers({ all: false });
  
  const runningContainers = containersData?.items.filter(c => c.state === 'running') || [];
  
  // Fetch stats for each running container
  const statsQueries = useQuery({
    queryKey: ['container-stats-batch', runningContainers.map(c => c.id)],
    queryFn: async () => {
      const stats = await Promise.all(
        runningContainers.slice(0, 6).map(async (container) => {
          try {
            const stat = await api.get<ContainerStats>(`/v1/docker/containers/${container.id}/stats`);
            return { name: container.name, ...stat };
          } catch {
            return { name: container.name, cpu_percent: 0, memory_percent: 0 };
          }
        })
      );
      return stats;
    },
    enabled: runningContainers.length > 0,
    refetchInterval: 10000,
  });

  if (containersLoading || statsQueries.isLoading) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Lade Container-Daten...</div>
      </div>
    );
  }

  const data = statsQueries.data || [];

  if (data.length === 0) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <p className="text-gray-500">Keine laufenden Container</p>
      </div>
    );
  }

  const chartData = data.map(d => ({
    name: d.name.length > 10 ? d.name.slice(0, 10) + '...' : d.name,
    cpu: d.cpu_percent || 0,
    memory: d.memory_percent || 0,
  }));

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Container Ressourcen</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} angle={-20} textAnchor="end" height={50} />
            <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
              itemStyle={{ color: '#fff' }}
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} formatter={(value) => <span className="text-gray-300 text-sm">{value}</span>} />
            <Bar dataKey="cpu" name="CPU" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="memory" name="Memory" fill="#06b6d4" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
