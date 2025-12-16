import { useState } from 'react';
import {
  Activity,
  Box,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  PanelLeftClose,
  PanelLeft,
  X,
} from 'lucide-react';
import { useDashboardStats } from '@/hooks/useServices';
import { useDockerInfo } from '@/hooks/useDocker';
import { useUserStats } from '@/hooks/useUsers';
import { useAuditStats } from '@/hooks/useAudit';
import { useMonitoringStore } from '@/stores/monitoringStore';
import {
  ServiceHealthChart,
  ResponseTimeChart,
  UptimeChart,
  ContainerResourceChart,
  ActivityTimeline,
} from '@/components/charts';
import {
  MonitoringTree,
  RegionDetail,
  VerfahrenDetail,
  HostDetail,
} from '@/components/monitoring';

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

// Default Dashboard Content (Stats, Charts)
function DashboardOverview() {
  const { data: serviceStats } = useDashboardStats();
  const { data: dockerInfo } = useDockerInfo();
  const { data: userStats } = useUserStats();
  const { data: auditStats } = useAuditStats(7);

  return (
    <div className="space-y-6">
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

// Detail View based on Selection
function DetailView() {
  const { selection, setSelection } = useMonitoringStore();

  if (!selection) {
    return <DashboardOverview />;
  }

  switch (selection.type) {
    case 'region':
      return (
        <RegionDetail
          regionId={selection.id}
          onVerfahrenSelect={(verfahrenId) =>
            setSelection('verfahren', verfahrenId, [...selection.path, verfahrenId])
          }
        />
      );
    case 'verfahren':
      return (
        <VerfahrenDetail
          verfahrenId={selection.id}
          onHostSelect={(hostId) =>
            setSelection('host', hostId, [...selection.path, hostId])
          }
        />
      );
    case 'host':
      return (
        <HostDetail
          hostId={selection.id}
          onViewFullLogs={(hostId) => {
            // Navigation zu Logs-Seite könnte hier implementiert werden
            console.log('View full logs for:', hostId);
          }}
        />
      );
    default:
      return <DashboardOverview />;
  }
}

// Mobile Drawer Component
function MobileDrawer({
  isOpen,
  onClose,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Backdrop */}
      <div
        className={`
          fixed inset-0 bg-black/60 backdrop-blur-sm z-40
          transition-opacity duration-300 lg:hidden
          ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
        `}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`
          fixed top-0 left-0 h-full w-80 bg-gray-900 border-r border-gray-800 z-50
          transform transition-transform duration-300 ease-in-out lg:hidden
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-white">Monitoring</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>
        <div className="overflow-y-auto h-[calc(100%-65px)]">
          {children}
        </div>
      </div>
    </>
  );
}

export function Dashboard() {
  const { selection, clearSelection } = useMonitoringStore();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  // Breadcrumb-Pfad für Header
  const getBreadcrumb = () => {
    if (!selection) return null;

    const labels: Record<string, string> = {
      region: 'Region',
      verfahren: 'Verfahren',
      host: 'Host',
    };

    return (
      <div className="flex items-center gap-2 text-sm">
        <button
          onClick={clearSelection}
          className="text-gray-400 hover:text-white transition-colors"
        >
          Dashboard
        </button>
        <span className="text-gray-600">/</span>
        <span className="text-emma-400">{labels[selection.type]}</span>
      </div>
    );
  };

  return (
    <div className="flex h-full -m-6">
      {/* Mobile Drawer */}
      <MobileDrawer
        isOpen={isMobileDrawerOpen}
        onClose={() => setIsMobileDrawerOpen(false)}
      >
        <MonitoringTree
          onSelect={() => setIsMobileDrawerOpen(false)}
          className="h-full"
        />
      </MobileDrawer>

      {/* Desktop Sidebar */}
      <aside
        className={`
          hidden lg:flex flex-col border-r border-gray-800 bg-gray-900/50
          transition-all duration-300 ease-in-out flex-shrink-0
          ${isSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80'}
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Monitoring
          </h2>
          <button
            onClick={() => setIsSidebarCollapsed(true)}
            className="p-1.5 hover:bg-gray-800 rounded-lg transition-colors"
            title="Sidebar einklappen"
          >
            <PanelLeftClose size={18} className="text-gray-400" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <MonitoringTree className="h-full" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 animate-fade-in">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {/* Sidebar Toggle Buttons */}
              {isSidebarCollapsed && (
                <button
                  onClick={() => setIsSidebarCollapsed(false)}
                  className="hidden lg:flex p-2 hover:bg-gray-800 rounded-lg transition-colors"
                  title="Sidebar ausklappen"
                >
                  <PanelLeft size={20} className="text-gray-400" />
                </button>
              )}
              <button
                onClick={() => setIsMobileDrawerOpen(true)}
                className="lg:hidden p-2 hover:bg-gray-800 rounded-lg transition-colors"
                title="Monitoring-Tree öffnen"
              >
                <PanelLeft size={20} className="text-gray-400" />
              </button>

              <div>
                <h1 className="text-2xl font-bold text-white">Dashboard</h1>
                {selection ? (
                  getBreadcrumb()
                ) : (
                  <p className="text-gray-400 mt-1">Systemübersicht und Monitoring</p>
                )}
              </div>
            </div>

            {/* Back Button when selection active */}
            {selection && (
              <button
                onClick={clearSelection}
                className="btn-ghost text-sm"
              >
                Zurück zur Übersicht
              </button>
            )}
          </div>

          {/* Content Area */}
          <DetailView />
        </div>
      </main>
    </div>
  );
}
