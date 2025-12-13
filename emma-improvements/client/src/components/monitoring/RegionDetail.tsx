import { MapPin, Server, RefreshCw, CheckCircle, AlertTriangle, XCircle, Layers } from 'lucide-react';
import { useRegionDetails, useRefreshHost } from '@/hooks/useMonitoringHierarchy';
import type { Verfahren } from '@/types/monitoring';

interface RegionDetailProps {
  regionId: string;
  onVerfahrenSelect?: (verfahrenId: string) => void;
}

// Stats-Karte Komponente
function StatCard({ label, value, icon: Icon, color }: {
  label: string;
  value: number;
  icon: typeof Server;
  color: string;
}) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-xs text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  );
}

// Verfahren-Karte Komponente
function VerfahrenCard({ verfahren, onClick }: {
  verfahren: Verfahren;
  onClick: () => void;
}) {
  const statusConfig = {
    healthy: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-900/20 border-green-800' },
    degraded: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-800' },
    critical: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-900/20 border-red-800' },
  }[verfahren.aggregatedStatus] || { icon: Server, color: 'text-gray-400', bg: 'bg-gray-800 border-gray-700' };

  const StatusIcon = statusConfig.icon;

  const hostsOnline = verfahren.hosts.filter(h => h.status === 'online').length;
  const servicesTotal = verfahren.hosts.reduce((acc, h) => acc + h.services.length, 0);
  const servicesRunning = verfahren.hosts.reduce(
    (acc, h) => acc + h.services.filter(s => s.status === 'running').length,
    0
  );

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-lg border ${statusConfig.bg}
                  hover:bg-gray-700/50 transition-colors duration-200`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Layers size={20} className="text-gray-500" />
          <div>
            <p className="font-semibold text-white">{verfahren.code}</p>
            <p className="text-sm text-gray-400">{verfahren.name}</p>
          </div>
        </div>
        <StatusIcon size={20} className={statusConfig.color} />
      </div>

      <div className="mt-3 flex gap-4 text-xs">
        <span className="text-gray-400">
          <span className="text-white font-medium">{hostsOnline}</span>/{verfahren.hosts.length} Hosts
        </span>
        <span className="text-gray-400">
          <span className="text-white font-medium">{servicesRunning}</span>/{servicesTotal} Services
        </span>
      </div>
    </button>
  );
}

// Skeleton Loading
function RegionDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 bg-gray-700 rounded-xl" />
        <div className="space-y-2">
          <div className="h-6 w-40 bg-gray-700 rounded" />
          <div className="h-4 w-24 bg-gray-700 rounded" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 bg-gray-700 rounded-lg" />
        ))}
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-24 bg-gray-700 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export function RegionDetail({ regionId, onVerfahrenSelect }: RegionDetailProps) {
  const { data: region, isLoading, error } = useRegionDetails(regionId);
  const refreshHost = useRefreshHost();

  if (isLoading) {
    return (
      <div className="card p-6">
        <RegionDetailSkeleton />
      </div>
    );
  }

  if (error || !region) {
    return (
      <div className="card p-6">
        <div className="text-center py-8">
          <XCircle size={48} className="mx-auto text-red-400 mb-3" />
          <p className="text-red-400">Region nicht gefunden</p>
        </div>
      </div>
    );
  }

  // Aggregierte Statistiken berechnen
  const hostsOnline = region.verfahren.reduce(
    (acc, v) => acc + v.hosts.filter(h => h.status === 'online').length,
    0
  );
  const hostsOffline = region.verfahren.reduce(
    (acc, v) => acc + v.hosts.filter(h => h.status === 'offline').length,
    0
  );
  const totalServices = region.verfahren.reduce(
    (acc, v) => acc + v.hosts.reduce((a, h) => a + h.services.length, 0),
    0
  );

  const handleRefreshAll = async () => {
    const allHostIds = region.verfahren.flatMap(v => v.hosts.map(h => h.id));
    for (const hostId of allHostIds) {
      await refreshHost.mutateAsync(hostId);
    }
  };

  const statusColor = {
    healthy: 'text-green-400',
    degraded: 'text-yellow-400',
    critical: 'text-red-400',
  }[region.aggregatedStatus] || 'text-gray-400';

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="p-4 bg-blue-900/30 rounded-xl">
            <MapPin size={32} className="text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{region.name}</h2>
            <p className={`text-sm ${statusColor} capitalize`}>
              Status: {region.aggregatedStatus}
            </p>
          </div>
        </div>

        <button
          onClick={handleRefreshAll}
          disabled={refreshHost.isPending}
          className="btn-secondary text-sm"
        >
          <RefreshCw size={16} className={refreshHost.isPending ? 'animate-spin' : ''} />
          Alle aktualisieren
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Verfahren"
          value={region.verfahren.length}
          icon={Layers}
          color="bg-purple-900/30 text-purple-400"
        />
        <StatCard
          label="Hosts Online"
          value={hostsOnline}
          icon={CheckCircle}
          color="bg-green-900/30 text-green-400"
        />
        <StatCard
          label="Hosts Offline"
          value={hostsOffline}
          icon={XCircle}
          color="bg-red-900/30 text-red-400"
        />
        <StatCard
          label="Services"
          value={totalServices}
          icon={Server}
          color="bg-blue-900/30 text-blue-400"
        />
      </div>

      {/* Verfahren Liste */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          Verfahren ({region.verfahren.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {region.verfahren.map(verfahren => (
            <VerfahrenCard
              key={verfahren.id}
              verfahren={verfahren}
              onClick={() => onVerfahrenSelect?.(verfahren.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
