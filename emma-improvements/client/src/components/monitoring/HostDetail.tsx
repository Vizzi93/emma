import { useState } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Server,
  Cpu,
  HardDrive,
  MemoryStick,
  Clock,
  RefreshCw,
  FileText,
  Wifi,
  WifiOff,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import { useHostDetails, useRefreshHost, useCheckService } from '@/hooks/useMonitoringHierarchy';
import type { HostService, HostMetrics } from '@/types/monitoring';

interface HostDetailProps {
  hostId: string;
  onViewFullLogs?: (hostId: string) => void;
}

// Progress-Bar für Metriken
function MetricBar({ value, label, icon: Icon, color, threshold = { warning: 70, critical: 90 } }: {
  value: number;
  label: string;
  icon: typeof Cpu;
  color: string;
  threshold?: { warning: number; critical: number };
}) {
  const barColor = value >= threshold.critical
    ? 'bg-red-500'
    : value >= threshold.warning
    ? 'bg-yellow-500'
    : color;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-gray-400">
          <Icon size={14} />
          {label}
        </div>
        <span className={`font-semibold ${
          value >= threshold.critical ? 'text-red-400' :
          value >= threshold.warning ? 'text-yellow-400' :
          'text-white'
        }`}>
          {value.toFixed(1)}%
        </span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

// Service-Zeile Komponente
function ServiceRow({ service, onCheck }: {
  service: HostService;
  onCheck: () => void;
}) {
  const statusConfig = {
    running: { icon: CheckCircle, color: 'text-green-400', badge: 'badge-success' },
    stopped: { icon: XCircle, color: 'text-gray-400', badge: 'badge bg-gray-700 text-gray-300 border-gray-600' },
    error: { icon: AlertTriangle, color: 'text-red-400', badge: 'badge-error' },
  }[service.status] || { icon: XCircle, color: 'text-gray-400', badge: 'badge bg-gray-700 text-gray-300 border-gray-600' };

  const StatusIcon = statusConfig.icon;

  return (
    <div className="flex items-center justify-between py-2 px-3 bg-gray-800/30 rounded-lg">
      <div className="flex items-center gap-3">
        <StatusIcon size={16} className={statusConfig.color} />
        <div>
          <p className="text-sm font-medium text-white">{service.name}</p>
          <p className="text-xs text-gray-500">Port {service.port}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={statusConfig.badge}>{service.status}</span>
        <button
          onClick={onCheck}
          className="p-1.5 hover:bg-gray-700 rounded transition-colors"
          title="Service prüfen"
        >
          <RefreshCw size={14} className="text-gray-400 hover:text-white" />
        </button>
      </div>
    </div>
  );
}

// Log-Eintrag
interface LogEntry {
  timestamp: Date;
  level: 'info' | 'warning' | 'error';
  message: string;
}

function LogLine({ log }: { log: LogEntry }) {
  const levelConfig = {
    info: { color: 'text-blue-400', bg: 'bg-blue-900/20' },
    warning: { color: 'text-yellow-400', bg: 'bg-yellow-900/20' },
    error: { color: 'text-red-400', bg: 'bg-red-900/20' },
  }[log.level];

  return (
    <div className={`flex gap-3 py-1 px-2 rounded text-xs font-mono ${levelConfig.bg}`}>
      <span className="text-gray-500 flex-shrink-0">
        {format(log.timestamp, 'HH:mm:ss')}
      </span>
      <span className={`${levelConfig.color} uppercase w-12 flex-shrink-0`}>
        [{log.level}]
      </span>
      <span className="text-gray-300 truncate">{log.message}</span>
    </div>
  );
}

// Uptime-Formatierung
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

// Skeleton Loading
function HostDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 bg-gray-700 rounded-xl" />
        <div className="space-y-2 flex-1">
          <div className="h-6 w-40 bg-gray-700 rounded" />
          <div className="h-4 w-32 bg-gray-700 rounded" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-16 bg-gray-700 rounded-lg" />
        ))}
      </div>
      <div className="h-48 bg-gray-700 rounded-lg" />
    </div>
  );
}

export function HostDetail({ hostId, onViewFullLogs }: HostDetailProps) {
  const { data: host, isLoading, error } = useHostDetails(hostId);
  const refreshHost = useRefreshHost();
  const checkService = useCheckService();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Dummy-Logs (in Produktion aus API)
  const dummyLogs: LogEntry[] = [
    { timestamp: new Date(Date.now() - 1000 * 60), level: 'info', message: 'Health check passed' },
    { timestamp: new Date(Date.now() - 1000 * 120), level: 'info', message: 'Connection established' },
    { timestamp: new Date(Date.now() - 1000 * 180), level: 'warning', message: 'High memory usage detected' },
    { timestamp: new Date(Date.now() - 1000 * 240), level: 'info', message: 'Service restarted successfully' },
    { timestamp: new Date(Date.now() - 1000 * 300), level: 'error', message: 'Connection timeout to database' },
    { timestamp: new Date(Date.now() - 1000 * 360), level: 'info', message: 'Backup completed' },
    { timestamp: new Date(Date.now() - 1000 * 420), level: 'info', message: 'SSL certificate valid' },
    { timestamp: new Date(Date.now() - 1000 * 480), level: 'warning', message: 'Disk space below 20%' },
    { timestamp: new Date(Date.now() - 1000 * 540), level: 'info', message: 'Service started' },
    { timestamp: new Date(Date.now() - 1000 * 600), level: 'info', message: 'Host initialized' },
  ];

  if (isLoading) {
    return (
      <div className="card p-6">
        <HostDetailSkeleton />
      </div>
    );
  }

  if (error || !host) {
    return (
      <div className="card p-6">
        <div className="text-center py-8">
          <XCircle size={48} className="mx-auto text-red-400 mb-3" />
          <p className="text-red-400">Host nicht gefunden</p>
        </div>
      </div>
    );
  }

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshHost.mutateAsync(hostId);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCheckService = async (serviceName: string) => {
    await checkService.mutateAsync({ hostId, serviceName });
  };

  const isOnline = host.status === 'online';
  const StatusIcon = isOnline ? Wifi : WifiOff;
  const statusColor = {
    online: 'text-green-400',
    offline: 'text-red-400',
    warning: 'text-yellow-400',
    unknown: 'text-gray-400',
  }[host.status] || 'text-gray-400';

  // Default-Metriken falls nicht vorhanden
  const metrics: HostMetrics = host.metrics || {
    cpu: 0,
    memory: 0,
    disk: 0,
    uptime: 0,
  };

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${isOnline ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
            <Server size={28} className={statusColor} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{host.name}</h2>
            <div className="flex items-center gap-3 mt-1">
              <code className="text-sm text-gray-400 bg-gray-800 px-2 py-0.5 rounded">
                {host.ip}
              </code>
              <div className={`flex items-center gap-1 text-sm ${statusColor}`}>
                <StatusIcon size={14} />
                <span className="capitalize">{host.status}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="btn-secondary text-sm"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            Ping
          </button>
        </div>
      </div>

      {/* Metriken */}
      {host.metrics && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            System-Metriken
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricBar
              value={metrics.cpu}
              label="CPU"
              icon={Cpu}
              color="bg-blue-500"
            />
            <MetricBar
              value={metrics.memory}
              label="RAM"
              icon={MemoryStick}
              color="bg-purple-500"
            />
            <MetricBar
              value={metrics.disk}
              label="Disk"
              icon={HardDrive}
              color="bg-cyan-500"
            />
          </div>

          {/* Uptime */}
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock size={14} />
            <span>Uptime: </span>
            <span className="text-white font-medium">{formatUptime(metrics.uptime)}</span>
          </div>
        </div>
      )}

      {/* Letzter Check */}
      <div className="text-sm text-gray-400">
        Letzter Check:{' '}
        <span className="text-white">
          {formatDistanceToNow(new Date(host.lastCheck), { addSuffix: true, locale: de })}
        </span>
      </div>

      {/* Services */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Services ({host.services.length})
          </h3>
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1 text-green-400">
              <CheckCircle size={12} />
              {host.services.filter(s => s.status === 'running').length}
            </span>
            <span className="flex items-center gap-1 text-red-400">
              <XCircle size={12} />
              {host.services.filter(s => s.status !== 'running').length}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          {host.services.map(service => (
            <ServiceRow
              key={service.name}
              service={service}
              onCheck={() => handleCheckService(service.name)}
            />
          ))}

          {host.services.length === 0 && (
            <div className="text-center py-4 text-gray-500 text-sm">
              Keine Services konfiguriert
            </div>
          )}
        </div>
      </div>

      {/* Logs Preview */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Letzte Logs
          </h3>
          {onViewFullLogs && (
            <button
              onClick={() => onViewFullLogs(hostId)}
              className="text-xs text-emma-400 hover:text-emma-300 flex items-center gap-1"
            >
              Alle anzeigen
              <ExternalLink size={12} />
            </button>
          )}
        </div>

        <div className="bg-gray-900 rounded-lg p-3 space-y-1 max-h-48 overflow-y-auto">
          {dummyLogs.map((log, i) => (
            <LogLine key={i} log={log} />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2 border-t border-gray-700">
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-secondary text-sm flex-1"
        >
          <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
          Host aktualisieren
        </button>
        {onViewFullLogs && (
          <button
            onClick={() => onViewFullLogs(hostId)}
            className="btn-ghost text-sm"
          >
            <FileText size={16} />
            Vollständige Logs
          </button>
        )}
      </div>
    </div>
  );
}
