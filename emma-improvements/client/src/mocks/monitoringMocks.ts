import type {
  MonitoringHierarchy,
  Region,
  Verfahren,
  Host,
  HostService,
  HostMetrics,
} from '@/types/monitoring';

// ============================================================================
// Helper Functions
// ============================================================================

function randomId(): string {
  return Math.random().toString(36).substring(2, 11);
}

function randomBetween(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomFloat(min: number, max: number, decimals: number = 1): number {
  const value = Math.random() * (max - min) + min;
  return Number(value.toFixed(decimals));
}

function randomFromArray<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function weightedRandom<T>(options: { value: T; weight: number }[]): T {
  const totalWeight = options.reduce((sum, opt) => sum + opt.weight, 0);
  let random = Math.random() * totalWeight;

  for (const option of options) {
    random -= option.weight;
    if (random <= 0) return option.value;
  }

  return options[options.length - 1].value;
}

// ============================================================================
// Service Templates
// ============================================================================

const SERVICE_TEMPLATES: Array<{ name: string; port: number }> = [
  { name: 'nginx', port: 80 },
  { name: 'nginx-ssl', port: 443 },
  { name: 'postgresql', port: 5432 },
  { name: 'mysql', port: 3306 },
  { name: 'redis', port: 6379 },
  { name: 'node-app', port: 3000 },
  { name: 'node-api', port: 3001 },
  { name: 'docker', port: 2375 },
  { name: 'ssh', port: 22 },
  { name: 'prometheus', port: 9090 },
  { name: 'grafana', port: 3000 },
  { name: 'elasticsearch', port: 9200 },
  { name: 'rabbitmq', port: 5672 },
  { name: 'mongodb', port: 27017 },
  { name: 'memcached', port: 11211 },
];

// ============================================================================
// Host Name Templates
// ============================================================================

const HOST_PREFIXES = [
  'srv', 'app', 'web', 'db', 'api', 'cache', 'worker', 'proxy', 'lb', 'mon',
];

const HOST_ROLES = [
  'master', 'slave', 'primary', 'replica', 'node', 'backend', 'frontend',
];

function generateHostname(index: number): string {
  const prefix = randomFromArray(HOST_PREFIXES);
  const role = randomFromArray(HOST_ROLES);
  const num = String(index).padStart(2, '0');

  // Different naming patterns
  const patterns = [
    `${prefix}-${role}-${num}`,
    `${prefix}${num}-${role}`,
    `${prefix}-${num}`,
    `${role}-${prefix}-${num}`,
  ];

  return randomFromArray(patterns);
}

function generateIP(regionIndex: number, verfahrenIndex: number, hostIndex: number): string {
  const octet1 = 10 + regionIndex;
  const octet2 = 100 + verfahrenIndex * 10;
  const octet3 = hostIndex + 1;
  return `${octet1}.${octet2}.${octet3}.${randomBetween(1, 254)}`;
}

// ============================================================================
// Generator Functions
// ============================================================================

function generateServices(hostStatus: Host['status']): HostService[] {
  const numServices = randomBetween(2, 6);
  const selectedTemplates = [...SERVICE_TEMPLATES]
    .sort(() => Math.random() - 0.5)
    .slice(0, numServices);

  return selectedTemplates.map((template) => {
    let status: HostService['status'];

    if (hostStatus === 'offline') {
      status = 'stopped';
    } else if (hostStatus === 'warning') {
      status = weightedRandom([
        { value: 'running', weight: 60 },
        { value: 'error', weight: 30 },
        { value: 'stopped', weight: 10 },
      ]);
    } else {
      status = weightedRandom([
        { value: 'running', weight: 95 },
        { value: 'error', weight: 3 },
        { value: 'stopped', weight: 2 },
      ]);
    }

    return {
      name: template.name,
      port: template.port,
      status,
    };
  });
}

function generateMetrics(hostStatus: Host['status']): HostMetrics {
  if (hostStatus === 'offline') {
    return { cpu: 0, memory: 0, disk: 0, uptime: 0 };
  }

  const isHighLoad = hostStatus === 'warning';

  return {
    cpu: isHighLoad ? randomFloat(70, 95) : randomFloat(5, 65),
    memory: isHighLoad ? randomFloat(75, 95) : randomFloat(20, 70),
    disk: randomFloat(30, 85),
    uptime: randomBetween(3600, 86400 * 90), // 1 hour to 90 days in seconds
  };
}

function generateHost(
  regionIndex: number,
  verfahrenIndex: number,
  hostIndex: number
): Host {
  // Status distribution: 80% online, 15% warning, 5% offline
  const status = weightedRandom<Host['status']>([
    { value: 'online', weight: 80 },
    { value: 'warning', weight: 15 },
    { value: 'offline', weight: 5 },
  ]);

  const lastCheckOffset = randomBetween(0, 300000); // 0-5 minutes ago

  return {
    id: `host-${randomId()}`,
    name: generateHostname(hostIndex + 1),
    ip: generateIP(regionIndex, verfahrenIndex, hostIndex),
    status,
    lastCheck: new Date(Date.now() - lastCheckOffset),
    services: generateServices(status),
    metrics: generateMetrics(status),
  };
}

function calculateAggregatedStatus(
  items: Array<Host | Verfahren | { status: string }>
): 'healthy' | 'degraded' | 'critical' {
  const statuses = items.map((item) => {
    if ('aggregatedStatus' in item) return item.aggregatedStatus;
    // For hosts
    const hostStatus = (item as Host).status;
    if (hostStatus === 'offline') return 'critical';
    if (hostStatus === 'warning') return 'degraded';
    return 'healthy';
  });

  if (statuses.some((s) => s === 'critical')) return 'critical';
  if (statuses.some((s) => s === 'degraded')) return 'degraded';
  return 'healthy';
}

function generateVerfahren(
  regionIndex: number,
  verfahrenIndex: number,
  code: string,
  name: string,
  description?: string
): Verfahren {
  const numHosts = randomBetween(5, 15);
  const hosts: Host[] = [];

  for (let i = 0; i < numHosts; i++) {
    hosts.push(generateHost(regionIndex, verfahrenIndex, i));
  }

  return {
    id: `verfahren-${randomId()}`,
    code,
    name,
    description,
    hosts,
    aggregatedStatus: calculateAggregatedStatus(hosts),
  };
}

// ============================================================================
// Region Data
// ============================================================================

const REGION_DATA: Array<{
  name: string;
  verfahren: Array<{ code: string; name: string; description?: string }>;
}> = [
  {
    name: 'Bremerhaven',
    verfahren: [
      {
        code: 'Mastu_BHV001',
        name: 'Masterumgebung BHV',
        description: 'Primäre Produktionsumgebung Bremerhaven',
      },
      {
        code: 'Mastu_BHV002',
        name: 'Masterumgebung BHV Backup',
        description: 'Disaster Recovery Umgebung',
      },
      {
        code: 'Fila_BHV001',
        name: 'Fileablage BHV',
        description: 'Zentrale Dokumentenverwaltung',
      },
      {
        code: 'Web_BHV001',
        name: 'Webservices BHV',
        description: 'Öffentliche Webportale',
      },
    ],
  },
  {
    name: 'Hamburg',
    verfahren: [
      {
        code: 'Mastu_HH001',
        name: 'Masterumgebung Hamburg',
        description: 'Hauptrechenzentrum Hamburg',
      },
      {
        code: 'Fila_HH001',
        name: 'Fileablage Hamburg',
        description: 'Archivierung und Dokumentation',
      },
      {
        code: 'API_HH001',
        name: 'API Gateway Hamburg',
        description: 'Zentrale API-Verwaltung',
      },
    ],
  },
  {
    name: 'Niedersachsen',
    verfahren: [
      {
        code: 'Mastu_NL001',
        name: 'Masterumgebung Niedersachsen',
        description: 'Produktionsumgebung NDS',
      },
      {
        code: 'Mastu_NL002',
        name: 'Test-Umgebung NDS',
        description: 'Staging und QA Systeme',
      },
      {
        code: 'Fila_NL001',
        name: 'Fileablage NDS',
        description: 'Zentrale Dateiablage Niedersachsen',
      },
      {
        code: 'DB_NL001',
        name: 'Datenbank Cluster NDS',
        description: 'PostgreSQL HA Cluster',
      },
    ],
  },
];

// ============================================================================
// Generate Mock Data
// ============================================================================

function generateMockHierarchy(): MonitoringHierarchy {
  const regions: Region[] = REGION_DATA.map((regionData, regionIndex) => {
    const verfahren: Verfahren[] = regionData.verfahren.map((v, verfahrenIndex) =>
      generateVerfahren(regionIndex, verfahrenIndex, v.code, v.name, v.description)
    );

    return {
      id: `region-${randomId()}`,
      name: regionData.name,
      verfahren,
      aggregatedStatus: calculateAggregatedStatus(verfahren),
    };
  });

  return {
    regions,
    lastUpdated: new Date(),
  };
}

// ============================================================================
// Exported Mock Data
// ============================================================================

// Generate fresh data on import (for development)
export const MOCK_HIERARCHY: MonitoringHierarchy = generateMockHierarchy();

// Helper to regenerate mock data
export function regenerateMockHierarchy(): MonitoringHierarchy {
  return generateMockHierarchy();
}

// Get specific items from mock data
export function getMockRegion(regionId: string): Region | undefined {
  return MOCK_HIERARCHY.regions.find((r) => r.id === regionId);
}

export function getMockVerfahren(verfahrenId: string): Verfahren | undefined {
  for (const region of MOCK_HIERARCHY.regions) {
    const verfahren = region.verfahren.find((v) => v.id === verfahrenId);
    if (verfahren) return verfahren;
  }
  return undefined;
}

export function getMockHost(hostId: string): Host | undefined {
  for (const region of MOCK_HIERARCHY.regions) {
    for (const verfahren of region.verfahren) {
      const host = verfahren.hosts.find((h) => h.id === hostId);
      if (host) return host;
    }
  }
  return undefined;
}

// Stats helper
export function getMockStats() {
  let totalHosts = 0;
  let healthyHosts = 0;
  let warningHosts = 0;
  let offlineHosts = 0;

  for (const region of MOCK_HIERARCHY.regions) {
    for (const verfahren of region.verfahren) {
      for (const host of verfahren.hosts) {
        totalHosts++;
        if (host.status === 'online') healthyHosts++;
        else if (host.status === 'warning') warningHosts++;
        else if (host.status === 'offline') offlineHosts++;
      }
    }
  }

  return {
    totalRegions: MOCK_HIERARCHY.regions.length,
    totalVerfahren: MOCK_HIERARCHY.regions.reduce((acc, r) => acc + r.verfahren.length, 0),
    totalHosts,
    healthyHosts,
    warningHosts,
    offlineHosts,
  };
}
