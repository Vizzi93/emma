export interface Host {
  id: string;
  name: string;
  ip: string;
  status: 'online' | 'offline' | 'warning' | 'unknown';
  lastCheck: Date;
  services: HostService[];
  metrics?: HostMetrics;
}

export interface HostService {
  name: string;
  port: number;
  status: 'running' | 'stopped' | 'error';
}

export interface HostMetrics {
  cpu: number;
  memory: number;
  disk: number;
  uptime: number;
}

export interface Verfahren {
  id: string;
  code: string; // z.B. Mastu_NL001
  name: string;
  description?: string;
  hosts: Host[];
  aggregatedStatus: 'healthy' | 'degraded' | 'critical';
}

export interface Region {
  id: string;
  name: string; // z.B. Bremerhaven
  verfahren: Verfahren[];
  aggregatedStatus: 'healthy' | 'degraded' | 'critical';
}

export interface MonitoringHierarchy {
  regions: Region[];
  lastUpdated: Date;
}

// Helper-Types für Tree-Selection
export type SelectionType = 'region' | 'verfahren' | 'host';

export interface TreeSelection {
  type: SelectionType;
  id: string;
  path: string[]; // z.B. ['bremerhaven', 'mastu_nl001', 'host-01']
}
