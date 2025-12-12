import { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Activity, Plus, Search, Filter, RefreshCw, Globe, Server, Shield, Wifi,
  Play, Pause, Trash2, CheckCircle, AlertTriangle, XCircle, Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { useServices, useDashboardStats, useToggleService, useRunCheck, useDeleteService } from '@/hooks/useServices';
import type { Service, ServiceStatus, ServiceType } from '@/types/service';

const SERVICE_TYPE_ICONS: Record<ServiceType, typeof Globe> = {
  http: Globe, https: Shield, tcp: Server, ssl: Shield, dns: Wifi, ping: Activity,
};

const STATUS_CONFIG: Record<ServiceStatus, { color: string; bg: string; icon: typeof CheckCircle; label: string }> = {
  healthy: { color: 'text-green-400', bg: 'bg-green-900/30 border-green-700', icon: CheckCircle, label: 'Healthy' },
  degraded: { color: 'text-yellow-400', bg: 'bg-yellow-900/30 border-yellow-700', icon: AlertTriangle, label: 'Degraded' },
  unhealthy: { color: 'text-red-400', bg: 'bg-red-900/30 border-red-700', icon: XCircle, label: 'Unhealthy' },
  unknown: { color: 'text-gray-400', bg: 'bg-gray-800 border-gray-700', icon: Clock, label: 'Unknown' },
  paused: { color: 'text-gray-500', bg: 'bg-gray-800/50 border-gray-700', icon: Pause, label: 'Paused' },
};

export function Services() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const { data: servicesData, isLoading, refetch } = useServices();
  const { data: stats } = useDashboardStats();
  const toggleService = useToggleService();
  const runCheck = useRunCheck();
  const deleteService = useDeleteService();

  const services = servicesData?.items || [];
  const filteredServices = services.filter((service) => {
    const matchesSearch = service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.target.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || service.status === statusFilter;
    const matchesType = typeFilter === 'all' || service.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const handleToggle = async (service: Service) => {
    try {
      await toggleService.mutateAsync({ id: service.id, is_active: !service.is_active });
      toast.success(service.is_active ? 'Service pausiert' : 'Service aktiviert');
    } catch { toast.error('Fehler beim Umschalten'); }
  };

  const handleRunCheck = async (service: Service) => {
    try {
      await runCheck.mutateAsync(service.id);
      toast.success('Check ausgeführt');
    } catch { toast.error('Fehler beim Ausführen'); }
  };

  const handleDelete = async (service: Service) => {
    if (!confirm(`Service "${service.name}" wirklich löschen?`)) return;
    try {
      await deleteService.mutateAsync(service.id);
      toast.success('Service gelöscht');
    } catch { toast.error('Fehler beim Löschen'); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Services</h1>
          <p className="text-gray-400 mt-1">Überwache Endpoints, SSL-Zertifikate und Netzwerkdienste</p>
        </div>
        <button className="btn-primary"><Plus size={18} />Service hinzufügen</button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4"><div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emma-900/30 text-emma-400"><Activity size={20} /></div>
          <div><p className="text-2xl font-bold text-white">{stats?.total_services || 0}</p><p className="text-sm text-gray-400">Gesamt</p></div>
        </div></div>
        <div className="card p-4"><div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-900/30 text-green-400"><CheckCircle size={20} /></div>
          <div><p className="text-2xl font-bold text-white">{stats?.status_counts?.healthy || 0}</p><p className="text-sm text-gray-400">Healthy</p></div>
        </div></div>
        <div className="card p-4"><div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-yellow-900/30 text-yellow-400"><AlertTriangle size={20} /></div>
          <div><p className="text-2xl font-bold text-white">{(stats?.status_counts?.degraded || 0) + (stats?.status_counts?.unhealthy || 0)}</p><p className="text-sm text-gray-400">Probleme</p></div>
        </div></div>
        <div className="card p-4"><div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-900/30 text-purple-400"><Clock size={20} /></div>
          <div><p className="text-2xl font-bold text-white">{stats?.avg_response_time_ms ? `${Math.round(stats.avg_response_time_ms)}ms` : '-'}</p><p className="text-sm text-gray-400">Ø Response</p></div>
        </div></div>
      </div>

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Suche..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" />
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input w-36">
            <option value="all">Alle Status</option><option value="healthy">Healthy</option><option value="degraded">Degraded</option><option value="unhealthy">Unhealthy</option><option value="paused">Paused</option>
          </select>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="input w-32">
            <option value="all">Alle Typen</option><option value="http">HTTP</option><option value="https">HTTPS</option><option value="tcp">TCP</option><option value="ssl">SSL</option><option value="dns">DNS</option>
          </select>
          <button onClick={() => refetch()} className="btn-ghost"><RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} /></button>
        </div>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="card p-8 text-center text-gray-400"><RefreshCw size={24} className="mx-auto animate-spin mb-2" />Lade Services...</div>
        ) : filteredServices.length > 0 ? (
          filteredServices.map((service) => {
            const statusConfig = STATUS_CONFIG[service.status];
            const StatusIcon = statusConfig.icon;
            return (
              <div key={service.id} className={`card p-4 border ${statusConfig.bg} transition-all hover:border-gray-600`}>
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg bg-gray-800 ${statusConfig.color}`}><StatusIcon size={24} /></div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold text-white">{service.name}</span>
                      <span className="px-2 py-0.5 text-xs rounded bg-gray-800 text-gray-400 uppercase">{service.type}</span>
                      {!service.is_active && <span className="px-2 py-0.5 text-xs rounded bg-gray-700 text-gray-500">Pausiert</span>}
                    </div>
                    <p className="text-sm text-gray-400 truncate">{service.target}</p>
                  </div>
                  <div className="hidden md:flex items-center gap-6 text-sm">
                    <div className="text-center"><p className="text-white font-medium">{service.uptime_percentage.toFixed(1)}%</p><p className="text-gray-500">Uptime</p></div>
                    <div className="text-center"><p className="text-white font-medium">{service.last_response_time_ms ? `${Math.round(service.last_response_time_ms)}ms` : '-'}</p><p className="text-gray-500">Response</p></div>
                    <div className="text-center"><p className="text-gray-400 text-xs">{service.last_check_at ? formatDistanceToNow(new Date(service.last_check_at), { addSuffix: true, locale: de }) : 'Nie'}</p><p className="text-gray-500">Letzter Check</p></div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => handleRunCheck(service)} disabled={!service.is_active} className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-800 rounded-lg disabled:opacity-50" title="Check ausführen"><Play size={18} /></button>
                    <button onClick={() => handleToggle(service)} className="p-2 text-gray-400 hover:text-yellow-400 hover:bg-gray-800 rounded-lg" title={service.is_active ? 'Pausieren' : 'Aktivieren'}>{service.is_active ? <Pause size={18} /> : <Play size={18} />}</button>
                    <button onClick={() => handleDelete(service)} className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg" title="Löschen"><Trash2 size={18} /></button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="card p-8 text-center">
            <Activity size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Services gefunden</p>
            <p className="text-sm text-gray-500 mt-1">{searchQuery || statusFilter !== 'all' ? 'Versuche andere Filter' : 'Füge deinen ersten Service hinzu'}</p>
          </div>
        )}
      </div>
    </div>
  );
}
