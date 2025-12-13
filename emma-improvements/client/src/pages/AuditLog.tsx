import { useState } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  FileText, Search, RefreshCw, CheckCircle, XCircle,
  User, Server, ChevronDown, ChevronRight,
  Activity, LogIn, LogOut, UserPlus, Key, Trash2, Play, Square,
} from 'lucide-react';

import { useAuditLogs, useAuditStats } from '@/hooks/useAudit';
import { ACTION_LABELS } from '@/types/audit';
import type { AuditLog } from '@/types/audit';

const ACTION_ICONS: Record<string, typeof LogIn> = {
  'auth.login': LogIn,
  'auth.login_failed': XCircle,
  'auth.logout': LogOut,
  'auth.register': UserPlus,
  'auth.password_change': Key,
  'auth.password_reset': Key,
  'user.create': UserPlus,
  'user.update': User,
  'user.delete': Trash2,
  'user.deactivate': XCircle,
  'user.activate': CheckCircle,
  'service.create': Server,
  'service.update': Server,
  'service.delete': Trash2,
  'service.check': Activity,
  'container.start': Play,
  'container.stop': Square,
  'container.restart': RefreshCw,
  'container.remove': Trash2,
};

const CATEGORY_COLORS: Record<string, string> = {
  auth: 'text-blue-400 bg-blue-900/30',
  user: 'text-purple-400 bg-purple-900/30',
  service: 'text-green-400 bg-green-900/30',
  container: 'text-orange-400 bg-orange-900/30',
  system: 'text-gray-400 bg-gray-800',
};

function getCategory(action: string): string {
  return action.split('.')[0] || 'system';
}

function AuditLogRow({ log }: { log: AuditLog }) {
  const [expanded, setExpanded] = useState(false);
  const category = getCategory(log.action);
  const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.system;
  const Icon = ACTION_ICONS[log.action] || FileText;
  const label = ACTION_LABELS[log.action] || log.action;

  return (
    <div className={`card border ${log.success ? 'border-gray-800' : 'border-red-900/50'} transition-all`}>
      <div 
        className="p-4 flex items-center gap-4 cursor-pointer hover:bg-gray-800/30"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`p-2 rounded-lg ${colorClass}`}>
          <Icon size={18} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white">{label}</span>
            {!log.success && (
              <span className="px-2 py-0.5 text-xs rounded bg-red-900/50 text-red-400">Fehler</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm text-gray-400 mt-1">
            {log.user_email && <span>{log.user_email}</span>}
            {log.resource_id && (
              <span className="text-gray-500">
                {log.resource_type}: {log.resource_id.slice(0, 8)}...
              </span>
            )}
          </div>
        </div>

        <div className="hidden md:block text-right text-sm">
          <p className="text-gray-400">{formatDistanceToNow(new Date(log.created_at), { addSuffix: true, locale: de })}</p>
          <p className="text-gray-500 text-xs">{format(new Date(log.created_at), 'dd.MM.yyyy HH:mm')}</p>
        </div>

        <div className="text-gray-500">
          {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800 pt-3 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-500">IP-Adresse</p>
              <p className="text-gray-300">{log.ip_address || '-'}</p>
            </div>
            <div>
              <p className="text-gray-500">Zeitpunkt</p>
              <p className="text-gray-300">{format(new Date(log.created_at), 'PPpp', { locale: de })}</p>
            </div>
          </div>
          
          {log.description && (
            <div className="mt-3">
              <p className="text-gray-500">Beschreibung</p>
              <p className="text-gray-300">{log.description}</p>
            </div>
          )}
          
          {log.error_message && (
            <div className="mt-3">
              <p className="text-gray-500">Fehler</p>
              <p className="text-red-400">{log.error_message}</p>
            </div>
          )}
          
          {(log.old_values || log.new_values) && (
            <div className="mt-3 grid grid-cols-2 gap-4">
              {log.old_values && (
                <div>
                  <p className="text-gray-500 mb-1">Vorher</p>
                  <pre className="text-xs bg-gray-900 p-2 rounded overflow-auto max-h-32">
                    {JSON.stringify(log.old_values, null, 2)}
                  </pre>
                </div>
              )}
              {log.new_values && (
                <div>
                  <p className="text-gray-500 mb-1">Nachher</p>
                  <pre className="text-xs bg-gray-900 p-2 rounded overflow-auto max-h-32">
                    {JSON.stringify(log.new_values, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AuditLogPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [successFilter, setSuccessFilter] = useState<string>('all');

  const { data: logsData, isLoading, refetch } = useAuditLogs({
    search: searchQuery || undefined,
    action: categoryFilter !== 'all' ? categoryFilter : undefined,
    success: successFilter === 'all' ? undefined : successFilter === 'success',
    limit: 100,
  });
  const { data: stats } = useAuditStats(7);

  const logs = logsData?.items || [];

  // Get unique actions for filter
  const actionOptions = Object.keys(ACTION_LABELS);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Log</h1>
          <p className="text-gray-400 mt-1">Alle Systemaktivitäten protokolliert</p>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emma-900/30 text-emma-400"><FileText size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.total_events}</p><p className="text-sm text-gray-400">Events (7 Tage)</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-900/30 text-green-400"><CheckCircle size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.successful}</p><p className="text-sm text-gray-400">Erfolgreich</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-900/30 text-red-400"><XCircle size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.failed}</p><p className="text-sm text-gray-400">Fehlgeschlagen</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-900/30 text-purple-400"><User size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.unique_users}</p><p className="text-sm text-gray-400">Aktive User</p></div>
          </div></div>
        </div>
      )}

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Suche..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" />
          </div>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="input w-44">
            <option value="all">Alle Aktionen</option>
            {actionOptions.map((action) => (
              <option key={action} value={action}>{ACTION_LABELS[action]}</option>
            ))}
          </select>
          <select value={successFilter} onChange={(e) => setSuccessFilter(e.target.value)} className="input w-36">
            <option value="all">Alle Status</option>
            <option value="success">Erfolgreich</option>
            <option value="failed">Fehlgeschlagen</option>
          </select>
          <button onClick={() => refetch()} className="btn-ghost">
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {isLoading ? (
          <div className="card p-8 text-center text-gray-400">
            <RefreshCw size={24} className="mx-auto animate-spin mb-2" />Lade Logs...
          </div>
        ) : logs.length > 0 ? (
          logs.map((log) => <AuditLogRow key={log.id} log={log} />)
        ) : (
          <div className="card p-8 text-center">
            <FileText size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Audit-Logs gefunden</p>
          </div>
        )}
      </div>
    </div>
  );
}
