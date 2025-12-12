import { Activity, Server, Box, Users, AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import { useDashboardStats } from '@/hooks/useServices';
import { useDockerInfo } from '@/hooks/useDocker';
import { useUserStats } from '@/hooks/useUsers';
import { useAuditStats } from '@/hooks/useAudit';
import {
  ServiceHealthChart,
  ResponseTimeChart,
  UptimeChart,
  ContainerResourceChart,
  ActivityTimeline,
} from '@/components/charts';

function StatCard({ title, value, subtitle, icon: Icon, color }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: typeof Activity;
  color: string;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon size={24} />
        </div>
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

function AlertBanner({ healthy, degraded, unhealthy }: { healthy: number; degraded: number; unhealthy: number }) {
  if (unhealthy > 0) {
    return (
      <div className="bg-red-900/30 border border-red-800 rounded-xl p-4 flex items-center gap-3">
        <AlertTriangle className="text-red-400" size={24} />
        <div>
          <p className="font-semibold text-red-400">{unhealthy} Service{unhealthy > 1 ? 's' : ''} nicht erreichbar</p>
          <p className="text-sm text-red-300/70">Bitte prüfen Sie die Konfiguration</p>
        </div>
      </div>
    );
  }
  
  if (degraded > 0) {
    return (
      <div className="bg-yellow-900/30 border border-yellow-800 rounded-xl p-4 flex items-center gap-3">
        <Clock className="text-yellow-400" size={24} />
        <div>
          <p className="font-semibold text-yellow-400">{degraded} Service{degraded > 1 ? 's' : ''} instabil</p>
          <p className="text-sm text-yellow-300/70">Einzelne Checks fehlgeschlagen</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-green-900/30 border border-green-800 rounded-xl p-4 flex items-center gap-3">
      <CheckCircle className="text-green-400" size={24} />
      <div>
        <p className="font-semibold text-green-400">Alle Systeme operativ</p>
        <p className="text-sm text-green-300/70">{healthy} Services online</p>
      </div>
    </div>
  );
}

export function Dashboard() {
  const { data: serviceStats } = useDashboardStats();
  const { data: dockerInfo } = useDockerInfo();
  const { data: userStats } = useUserStats();
  const { data: auditStats } = useAuditStats(7);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Systemübersicht und Monitoring</p>
      </div>

      {/* Alert Banner */}
      {serviceStats && (
        <AlertBanner
          healthy={serviceStats.healthy_count}
          degraded={serviceStats.degraded_count}
          unhealthy={serviceStats.unhealthy_count}
        />
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Services"
          value={serviceStats?.total_services || 0}
          subtitle={`${serviceStats?.healthy_count || 0} healthy`}
          icon={Activity}
          color="bg-emma-900/30 text-emma-400"
        />
        <StatCard
          title="Container"
          value={dockerInfo?.containers_running || 0}
          subtitle={`von ${dockerInfo?.containers || 0} gesamt`}
          icon={Box}
          color="bg-orange-900/30 text-orange-400"
        />
        <StatCard
          title="Benutzer"
          value={userStats?.active_users || 0}
          subtitle={`${userStats?.active_sessions || 0} Sessions`}
          icon={Users}
          color="bg-purple-900/30 text-purple-400"
        />
        <StatCard
          title="Events (7d)"
          value={auditStats?.total_events || 0}
          subtitle={`${auditStats?.failed || 0} Fehler`}
          icon={TrendingUp}
          color="bg-cyan-900/30 text-cyan-400"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ServiceHealthChart />
        <UptimeChart />
        <ResponseTimeChart />
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ContainerResourceChart />
        <ActivityTimeline />
      </div>

      {/* Quick Info */}
      {dockerInfo && (
        <div className="card p-5">
          <h3 className="text-lg font-semibold text-white mb-3">System Info</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Docker Version</p>
              <p className="text-white font-medium">{dockerInfo.docker_version}</p>
            </div>
            <div>
              <p className="text-gray-500">OS</p>
              <p className="text-white font-medium">{dockerInfo.os}</p>
            </div>
            <div>
              <p className="text-gray-500">CPUs</p>
              <p className="text-white font-medium">{dockerInfo.cpus}</p>
            </div>
            <div>
              <p className="text-gray-500">Images</p>
              <p className="text-white font-medium">{dockerInfo.images}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
