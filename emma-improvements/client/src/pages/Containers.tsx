import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Box, Play, Square, RotateCcw, Trash2, RefreshCw, Search,
  Cpu, HardDrive, Network, AlertTriangle, CheckCircle, Clock, Pause,
} from 'lucide-react';
import toast from 'react-hot-toast';

import {
  useContainers, useDockerInfo, useStartContainer, useStopContainer,
  useRestartContainer, useRemoveContainer, useContainerStats,
} from '@/hooks/useDocker';
import type { Container, ContainerState } from '@/types/docker';

const STATE_CONFIG: Record<ContainerState, { color: string; bg: string; icon: typeof CheckCircle; label: string }> = {
  running: { color: 'text-green-400', bg: 'bg-green-900/30 border-green-700', icon: CheckCircle, label: 'Running' },
  paused: { color: 'text-yellow-400', bg: 'bg-yellow-900/30 border-yellow-700', icon: Pause, label: 'Paused' },
  restarting: { color: 'text-blue-400', bg: 'bg-blue-900/30 border-blue-700', icon: RotateCcw, label: 'Restarting' },
  exited: { color: 'text-red-400', bg: 'bg-red-900/30 border-red-700', icon: Square, label: 'Exited' },
  dead: { color: 'text-red-500', bg: 'bg-red-900/30 border-red-700', icon: AlertTriangle, label: 'Dead' },
  created: { color: 'text-gray-400', bg: 'bg-gray-800 border-gray-700', icon: Clock, label: 'Created' },
  removing: { color: 'text-orange-400', bg: 'bg-orange-900/30 border-orange-700', icon: Trash2, label: 'Removing' },
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function ContainerRow({ container }: { container: Container }) {
  const { data: stats } = useContainerStats(container.state === 'running' ? container.id : '');
  const startContainer = useStartContainer();
  const stopContainer = useStopContainer();
  const restartContainer = useRestartContainer();
  const removeContainer = useRemoveContainer();

  const stateConfig = STATE_CONFIG[container.state] || STATE_CONFIG.created;
  const StateIcon = stateConfig.icon;

  const handleStart = async () => {
    try {
      await startContainer.mutateAsync(container.id);
      toast.success(`${container.name} gestartet`);
    } catch { toast.error('Start fehlgeschlagen'); }
  };

  const handleStop = async () => {
    try {
      await stopContainer.mutateAsync({ containerId: container.id });
      toast.success(`${container.name} gestoppt`);
    } catch { toast.error('Stop fehlgeschlagen'); }
  };

  const handleRestart = async () => {
    try {
      await restartContainer.mutateAsync({ containerId: container.id });
      toast.success(`${container.name} neugestartet`);
    } catch { toast.error('Neustart fehlgeschlagen'); }
  };

  const handleRemove = async () => {
    if (!confirm(`Container "${container.name}" wirklich löschen?`)) return;
    try {
      await removeContainer.mutateAsync({ containerId: container.id, force: true });
      toast.success(`${container.name} gelöscht`);
    } catch { toast.error('Löschen fehlgeschlagen'); }
  };

  return (
    <div className={`card p-4 border ${stateConfig.bg} transition-all hover:border-gray-600`}>
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg bg-gray-800 ${stateConfig.color}`}>
          <StateIcon size={24} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-white">{container.name}</span>
            <span className={`px-2 py-0.5 text-xs rounded ${stateConfig.bg} ${stateConfig.color}`}>
              {stateConfig.label}
            </span>
          </div>
          <p className="text-sm text-gray-400 truncate">{container.image}</p>
          <p className="text-xs text-gray-500">{container.short_id}</p>
        </div>

        {stats && container.state === 'running' && (
          <div className="hidden lg:flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Cpu size={14} className="text-gray-500" />
              <span className="text-white">{stats.cpu_percent.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <HardDrive size={14} className="text-gray-500" />
              <span className="text-white">{formatBytes(stats.memory_usage)}</span>
              <span className="text-gray-500">/ {formatBytes(stats.memory_limit)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Network size={14} className="text-gray-500" />
              <span className="text-white">↓{formatBytes(stats.network_rx)}</span>
              <span className="text-white">↑{formatBytes(stats.network_tx)}</span>
            </div>
          </div>
        )}

        <div className="hidden md:block text-right text-sm">
          <p className="text-gray-400">{container.status}</p>
          <p className="text-gray-500 text-xs">
            {container.started_at
              ? formatDistanceToNow(new Date(container.started_at), { addSuffix: true, locale: de })
              : '-'}
          </p>
        </div>

        <div className="flex items-center gap-1">
          {container.state !== 'running' ? (
            <button onClick={handleStart} disabled={startContainer.isPending}
              className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-800 rounded-lg disabled:opacity-50" title="Starten">
              <Play size={18} />
            </button>
          ) : (
            <button onClick={handleStop} disabled={stopContainer.isPending}
              className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-800 rounded-lg disabled:opacity-50" title="Stoppen">
              <Square size={18} />
            </button>
          )}
          <button onClick={handleRestart} disabled={restartContainer.isPending || container.state !== 'running'}
            className="p-2 text-gray-400 hover:text-blue-400 hover:bg-gray-800 rounded-lg disabled:opacity-50" title="Neustarten">
            <RotateCcw size={18} />
          </button>
          <button onClick={handleRemove} disabled={removeContainer.isPending}
            className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg disabled:opacity-50" title="Löschen">
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export function Containers() {
  const [searchQuery, setSearchQuery] = useState('');
  const [stateFilter, setStateFilter] = useState<string>('all');

  const { data: containersData, isLoading, refetch, error } = useContainers();
  const { data: dockerInfo } = useDockerInfo();

  const containers = containersData?.items || [];
  const filteredContainers = containers.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.image.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesState = stateFilter === 'all' || c.state === stateFilter;
    return matchesSearch && matchesState;
  });

  if (error) {
    return (
      <div className="card p-8 text-center">
        <AlertTriangle size={48} className="mx-auto text-yellow-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Docker nicht verfügbar</h2>
        <p className="text-gray-400">Stelle sicher, dass Docker läuft und aiodocker installiert ist.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Container</h1>
          <p className="text-gray-400 mt-1">Docker Container verwalten und überwachen</p>
        </div>
      </div>

      {dockerInfo && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emma-900/30 text-emma-400"><Box size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{dockerInfo.containers}</p><p className="text-sm text-gray-400">Container</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-900/30 text-green-400"><CheckCircle size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{dockerInfo.containers_running}</p><p className="text-sm text-gray-400">Running</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-900/30 text-red-400"><Square size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{dockerInfo.containers_stopped}</p><p className="text-sm text-gray-400">Stopped</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-900/30 text-purple-400"><HardDrive size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{dockerInfo.images}</p><p className="text-sm text-gray-400">Images</p></div>
          </div></div>
        </div>
      )}

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Suche..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" />
          </div>
          <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} className="input w-36">
            <option value="all">Alle Status</option>
            <option value="running">Running</option>
            <option value="exited">Exited</option>
            <option value="paused">Paused</option>
            <option value="created">Created</option>
          </select>
          <button onClick={() => refetch()} className="btn-ghost">
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="card p-8 text-center text-gray-400">
            <RefreshCw size={24} className="mx-auto animate-spin mb-2" />Lade Container...
          </div>
        ) : filteredContainers.length > 0 ? (
          filteredContainers.map((container) => <ContainerRow key={container.id} container={container} />)
        ) : (
          <div className="card p-8 text-center">
            <Box size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Container gefunden</p>
          </div>
        )}
      </div>
    </div>
  );
}
