import { useState } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  FileText, Search, RefreshCw, Download, ChevronDown, ChevronRight,
  User, Shield, Box, Settings, Key, LogIn, LogOut, AlertTriangle,
  Activity,
} from 'lucide-react';

import { useAuditLogs, useAuditStats, exportAuditLogs } from '@/hooks/useAudit';
import type { AuditLog, AuditFilters } from '@/types/audit';

const ACTION_ICONS: Record<string, typeof User> = {
  'user.login': LogIn,
  'user.logout': LogOut,
  'user.login_failed': AlertTriangle,
  'user.created': User,
  'user.updated': User,
  'user.deleted': User,
  'user.password_reset': Key,
  'user.role_changed': Shield,
  'service.created': Activity,
  'service.updated': Activity,
  'service.deleted': Activity,
  'container.started': Box,
  'container.stopped': Box,
  'container.restarted': Box,
  'settings.changed': Settings,
};

const ACTION_COLORS: Record<string, string> = {
  'user.login': 'text-green-400',
  'user.logout': 'text-gray-400',
  'user.login_failed': 'text-red-400',
  'user.created': 'text-blue-400',
  'user.deleted': 'text-red-400',
  'user.password_reset': 'text-yellow-400',
  'container.started': 'text-green-400',
  'container.stopped': 'text-red-400',
  'service.deleted': 'text-red-400',
};

function AuditLogRow({ log }: { log: AuditLog }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = ACTION_ICONS[log.action] || FileText;
  const color = ACTION_COLORS[log.action] || 'text-gray-400';

  return (
    <div className="card p-4 hover:bg-gray-800/50 transition-colors">
      <div className="flex items-center gap-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className={`p-2 rounded-lg bg-gray-800 ${color}`}>
          <Icon size={18} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-emma-400">{log.action}</span>
            {log.resource_type && (
              <span className="text-xs text-gray-500">
                {log.resource_type}{log.resource_id ? `: ${log.resource_id.slice(0, 8)}...` : ''}
              </span>
            )}
          </div>
          {log.description && <p className="text-sm text-gray-400 truncate">{log.description}</p>}
        </div>

        <div className="hidden md:block text-right">
          <p className="text-sm text-gray-300">{log.user_email || 'System'}</p>
          <p className="text-xs text-gray-500">{log.ip_address || '-'}</p>
        </div>

        <div className="text-right text-sm">
          <p className="text-gray-400">{formatDistanceToNow(new Date(log.created_at), { addSuffix: true, locale: de })}</p>
          <p className="text-xs text-gray-500">{format(new Date(log.created_at), 'HH:mm:ss')}</p>
        </div>

        <button className="p-1 text-gray-500">
          {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-800 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500 mb-1">Details</p>
            <p className="text-gray-300">User Agent: <span className="text-gray-500">{log.user_agent?.slice(0, 50) || '-'}...</span></p>
            <p className="text-gray-300">Request ID: <span className="font-mono text-gray-500">{log.request_id || '-'}</span></p>
          </div>
          {(log.old_values || log.new_values) && (
            <div>
              <p className="text-gray-500 mb-1">Änderungen</p>
              {log.old_values && (
                <div className="text-xs">
                  <span className="text-red-400">- </span>
                  <span className="text-gray-400">{JSON.stringify(log.old_values).slice(0, 100)}</span>
                </div>
              )}
              {log.new_values && (
                <div className="text-xs">
                  <span className="text-green-400">+ </span>
                  <span className="text-gray-400">{JSON.stringify(log.new_values).slice(0, 100)}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AuditLogs() {
  const [filters, setFilters] = useState<AuditFilters>({ limit: 50 });
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  
  const { data: logsData, isLoading, refetch } = useAuditLogs({
    ...filters,
    search: searchQuery || undefined,
    action: actionFilter || undefined,
  });
  const { data: stats } = useAuditStats(7);

  const logs = logsData?.items || [];
  const total = logsData?.total || 0;

  const handleExport = () => {
    exportAuditLogs({ action: actionFilter || undefined });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
          <p className="text-gray-400 mt-1">Aktivitäten und Änderungen nachverfolgen</p>
        </div>
        <button onClick={handleExport} className="btn-ghost">
          <Download size={18} /> CSV Export
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emma-900/30 text-emma-400"><FileText size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.total}</p><p className="text-sm text-gray-400">Letzte 7 Tage</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-900/30 text-green-400"><LogIn size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.by_action['user.login'] || 0}</p><p className="text-sm text-gray-400">Logins</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-900/30 text-blue-400"><User size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{Object.keys(stats.by_user).length}</p><p className="text-sm text-gray-400">Aktive User</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-900/30 text-red-400"><AlertTriangle size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.by_action['user.login_failed'] || 0}</p><p className="text-sm text-gray-400">Fehlgeschlagen</p></div>
          </div></div>
        </div>
      )}

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Suche in Beschreibung, E-Mail..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" />
          </div>
          <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} className="input w-48">
            <option value="">Alle Aktionen</option>
            <optgroup label="Auth">
              <option value="user.login">Login</option>
              <option value="user.logout">Logout</option>
              <option value="user.login_failed">Login fehlgeschlagen</option>
            </optgroup>
            <optgroup label="User">
              <option value="user.created">User erstellt</option>
              <option value="user.updated">User aktualisiert</option>
              <option value="user.deleted">User gelöscht</option>
              <option value="user.password_reset">Passwort Reset</option>
            </optgroup>
            <optgroup label="Services">
              <option value="service.created">Service erstellt</option>
              <option value="service.updated">Service aktualisiert</option>
              <option value="service.deleted">Service gelöscht</option>
            </optgroup>
            <optgroup label="Container">
              <option value="container.started">Container gestartet</option>
              <option value="container.stopped">Container gestoppt</option>
              <option value="container.restarted">Container neugestartet</option>
            </optgroup>
          </select>
          <button onClick={() => refetch()} className="btn-ghost">
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {isLoading ? (
          <div className="card p-8 text-center text-gray-400">
            <RefreshCw size={24} className="mx-auto animate-spin mb-2" />Lade Audit Logs...
          </div>
        ) : logs.length > 0 ? (
          <>
            {logs.map((log) => <AuditLogRow key={log.id} log={log} />)}
            {total > logs.length && (
              <div className="text-center py-4">
                <button 
                  onClick={() => setFilters({ ...filters, limit: (filters.limit || 50) + 50 })}
                  className="btn-ghost"
                >
                  Mehr laden ({total - logs.length} weitere)
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="card p-8 text-center">
            <FileText size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Audit Logs gefunden</p>
          </div>
        )}
      </div>
    </div>
  );
}
