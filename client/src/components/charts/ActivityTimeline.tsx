import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import { Activity, User, Server, Box, Shield, LogIn, AlertTriangle } from 'lucide-react';
import { useAuditLogs } from '@/hooks/useAudit';
import { ACTION_LABELS } from '@/types/audit';

const EVENT_ICONS: Record<string, typeof Activity> = {
  auth: LogIn,
  user: User,
  service: Server,
  container: Box,
  system: Shield,
};

const EVENT_COLORS: Record<string, string> = {
  auth: 'bg-blue-900/30 text-blue-400',
  user: 'bg-purple-900/30 text-purple-400',
  service: 'bg-green-900/30 text-green-400',
  container: 'bg-orange-900/30 text-orange-400',
  system: 'bg-gray-800 text-gray-400',
};

export function ActivityTimeline() {
  const { data: logsData, isLoading } = useAuditLogs({ limit: 8 });
  const logs = logsData?.items || [];

  if (isLoading) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Lade Aktivitäten...</div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="card p-6 h-72 flex items-center justify-center">
        <p className="text-gray-500">Keine Aktivitäten</p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Letzte Aktivitäten</h3>
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {logs.map((log) => {
          const category = log.action.split('.')[0];
          const Icon = EVENT_ICONS[category] || Activity;
          const colorClass = EVENT_COLORS[category] || EVENT_COLORS.system;
          const label = ACTION_LABELS[log.action] || log.action;

          return (
            <div key={log.id} className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${colorClass} flex-shrink-0`}>
                <Icon size={14} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">{label}</span>
                  {!log.success && <AlertTriangle size={12} className="text-red-400" />}
                </div>
                <p className="text-xs text-gray-400 truncate">
                  {log.user_email || 'System'} 
                  {log.resource_id && ` • ${log.resource_id.slice(0, 8)}...`}
                </p>
              </div>
              <span className="text-xs text-gray-500 flex-shrink-0">
                {formatDistanceToNow(new Date(log.created_at), { addSuffix: true, locale: de })}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
