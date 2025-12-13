import { useMemo } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Layers,
  Server,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Activity,
  ArrowUpDown,
} from 'lucide-react';
import { useVerfahrenDetails } from '@/hooks/useMonitoringHierarchy';
import type { HostService } from '@/types/monitoring';

interface VerfahrenDetailProps {
  verfahrenId: string;
  onHostSelect?: (hostId: string) => void;
}

// Mini-Sparkline für Response-Times (vereinfacht)
function Sparkline({ data, className = '' }: { data: number[]; className?: string }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - ((val - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 100 100" className={`h-6 w-16 ${className}`} preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Status-Badge Komponente
function StatusBadge({ status }: { status: string }) {
  const config = {
    online: { label: 'Online', class: 'badge-success' },
    offline: { label: 'Offline', class: 'badge-error' },
    warning: { label: 'Warnung', class: 'badge-warning' },
    unknown: { label: 'Unbekannt', class: 'badge bg-gray-700 text-gray-300 border-gray-600' },
    running: { label: 'Running', class: 'badge-success' },
    stopped: { label: 'Stopped', class: 'badge-error' },
    error: { label: 'Error', class: 'badge-error' },
  }[status] || { label: status, class: 'badge bg-gray-700 text-gray-300 border-gray-600' };

  return <span className={config.class}>{config.label}</span>;
}

// Service-Overview Mini-Liste
function ServiceOverview({ services }: { services: HostService[] }) {
  const running = services.filter(s => s.status === 'running').length;
  const stopped = services.filter(s => s.status === 'stopped').length;
  const errors = services.filter(s => s.status === 'error').length;

  return (
    <div className="flex items-center gap-2 text-xs">
      {running > 0 && (
        <span className="flex items-center gap-1 text-green-400">
          <CheckCircle size={12} />
          {running}
        </span>
      )}
      {stopped > 0 && (
        <span className="flex items-center gap-1 text-gray-400">
          <XCircle size={12} />
          {stopped}
        </span>
      )}
      {errors > 0 && (
        <span className="flex items-center gap-1 text-red-400">
          <AlertTriangle size={12} />
          {errors}
        </span>
      )}
    </div>
  );
}

// Skeleton Loading
function VerfahrenDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-gray-700 rounded-xl" />
        <div className="space-y-2">
          <div className="h-5 w-32 bg-gray-700 rounded" />
          <div className="h-4 w-48 bg-gray-700 rounded" />
        </div>
      </div>
      <div className="h-64 bg-gray-700 rounded-lg" />
    </div>
  );
}

export function VerfahrenDetail({ verfahrenId, onHostSelect }: VerfahrenDetailProps) {
  const { data: verfahren, isLoading, error } = useVerfahrenDetails(verfahrenId);

  // Sortierte Hosts: critical first, dann warning, dann online, dann name
  const sortedHosts = useMemo(() => {
    if (!verfahren?.hosts) return [];

    const statusPriority: Record<string, number> = {
      offline: 0,
      warning: 1,
      unknown: 2,
      online: 3,
    };

    return [...verfahren.hosts].sort((a, b) => {
      const priorityA = statusPriority[a.status] ?? 99;
      const priorityB = statusPriority[b.status] ?? 99;

      if (priorityA !== priorityB) {
        return priorityA - priorityB;
      }

      return a.name.localeCompare(b.name);
    });
  }, [verfahren?.hosts]);

  if (isLoading) {
    return (
      <div className="card p-6">
        <VerfahrenDetailSkeleton />
      </div>
    );
  }

  if (error || !verfahren) {
    return (
      <div className="card p-6">
        <div className="text-center py-8">
          <XCircle size={48} className="mx-auto text-red-400 mb-3" />
          <p className="text-red-400">Verfahren nicht gefunden</p>
        </div>
      </div>
    );
  }

  const statusColor = {
    healthy: 'text-green-400',
    degraded: 'text-yellow-400',
    critical: 'text-red-400',
  }[verfahren.aggregatedStatus] || 'text-gray-400';

  // Generiere Dummy-Response-Time-Daten (in Produktion aus API)
  const generateSparklineData = (hostId: string) => {
    // Seed basierend auf hostId für konsistente Daten
    const seed = hostId.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    return Array.from({ length: 10 }, (_, i) =>
      50 + Math.sin(seed + i) * 30 + Math.random() * 20
    );
  };

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-900/30 rounded-xl">
            <Layers size={28} className="text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{verfahren.code}</h2>
            <p className="text-sm text-gray-400">{verfahren.name}</p>
            {verfahren.description && (
              <p className="text-xs text-gray-500 mt-1">{verfahren.description}</p>
            )}
          </div>
        </div>

        <span className={`text-sm font-medium ${statusColor} capitalize`}>
          {verfahren.aggregatedStatus}
        </span>
      </div>

      {/* Stats-Leiste */}
      <div className="flex gap-6 py-3 border-y border-gray-700">
        <div className="flex items-center gap-2">
          <Server size={16} className="text-gray-500" />
          <span className="text-sm text-gray-400">
            <span className="text-white font-semibold">{verfahren.hosts.length}</span> Hosts
          </span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle size={16} className="text-green-500" />
          <span className="text-sm text-gray-400">
            <span className="text-white font-semibold">
              {verfahren.hosts.filter(h => h.status === 'online').length}
            </span> Online
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-gray-500" />
          <span className="text-sm text-gray-400">
            <span className="text-white font-semibold">
              {verfahren.hosts.reduce((acc, h) => acc + h.services.length, 0)}
            </span> Services
          </span>
        </div>
      </div>

      {/* Host-Tabelle */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">
            Hosts ({sortedHosts.length})
          </h3>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <ArrowUpDown size={12} />
            Sortiert nach Status
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Host</th>
                <th>IP</th>
                <th>Status</th>
                <th>Services</th>
                <th>Response</th>
                <th>Letzter Check</th>
              </tr>
            </thead>
            <tbody>
              {sortedHosts.map(host => (
                <tr
                  key={host.id}
                  onClick={() => onHostSelect?.(host.id)}
                  className="cursor-pointer hover:bg-gray-800/50"
                >
                  <td>
                    <div className="flex items-center gap-2">
                      <Server size={14} className="text-gray-500" />
                      <span className="font-medium text-white">{host.name}</span>
                    </div>
                  </td>
                  <td>
                    <code className="text-sm text-gray-400 bg-gray-800 px-2 py-0.5 rounded">
                      {host.ip}
                    </code>
                  </td>
                  <td>
                    <StatusBadge status={host.status} />
                  </td>
                  <td>
                    <ServiceOverview services={host.services} />
                  </td>
                  <td>
                    <Sparkline
                      data={generateSparklineData(host.id)}
                      className={
                        host.status === 'online' ? 'text-green-500' :
                        host.status === 'warning' ? 'text-yellow-500' :
                        'text-gray-500'
                      }
                    />
                  </td>
                  <td>
                    <div className="flex items-center gap-1 text-sm text-gray-400">
                      <Clock size={12} />
                      {formatDistanceToNow(new Date(host.lastCheck), {
                        addSuffix: true,
                        locale: de,
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {sortedHosts.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Keine Hosts vorhanden
          </div>
        )}
      </div>
    </div>
  );
}
