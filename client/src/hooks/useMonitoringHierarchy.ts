import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { MOCK_HIERARCHY } from '@/mocks/monitoringMocks';
import type {
  MonitoringHierarchy,
  Region,
  Verfahren,
  Host,
  HostService,
} from '@/types/monitoring';

// Query Keys
export const monitoringKeys = {
  all: ['monitoring'] as const,
  hierarchy: () => [...monitoringKeys.all, 'hierarchy'] as const,
  regions: () => [...monitoringKeys.all, 'regions'] as const,
  region: (id: string) => [...monitoringKeys.regions(), id] as const,
  verfahren: () => [...monitoringKeys.all, 'verfahren'] as const,
  verfahrenDetail: (id: string) => [...monitoringKeys.verfahren(), id] as const,
  hosts: () => [...monitoringKeys.all, 'hosts'] as const,
  host: (id: string) => [...monitoringKeys.hosts(), id] as const,
  hostServices: (id: string) => [...monitoringKeys.host(id), 'services'] as const,
};

// === Queries ===

/**
 * Haupt-Hook für die gesamte Monitoring-Hierarchie
 * Lädt alle Regionen mit Verfahren und Hosts
 */
export function useMonitoringHierarchy() {
  return useQuery({
    queryKey: monitoringKeys.hierarchy(),
    queryFn: async () => {
      // Falls VITE_USE_MOCKS gesetzt ist, direkt Mock-Daten verwenden
      if (import.meta.env.VITE_USE_MOCKS === 'true') {
        console.info('[Monitoring] Using mock data (VITE_USE_MOCKS=true)');
        return MOCK_HIERARCHY;
      }

      try {
        return await api.get<MonitoringHierarchy>('/v1/monitoring/hierarchy');
      } catch (error) {
        // Im Development-Modus bei Netzwerkfehlern auf Mock-Daten zurückfallen
        if (import.meta.env.DEV) {
          console.warn('[Monitoring] API not available, using mock data:', error);
          return MOCK_HIERARCHY;
        }
        throw error;
      }
    },
    refetchInterval: 30000, // 30s Auto-Refresh
    staleTime: 10000, // 10s stale time
  });
}

/**
 * Details einer einzelnen Region
 * Extrahiert die Daten aus der bereits geladenen Hierarchie.
 */
export function useRegionDetails(regionId: string) {
  const { data: hierarchy, isLoading: isHierarchyLoading } = useMonitoringHierarchy();

  const query = useQuery({
    queryKey: monitoringKeys.region(regionId),
    queryFn: async () => {
      // Aus der geladenen Hierarchie suchen
      if (hierarchy?.regions) {
        const region = hierarchy.regions.find((r) => r.id === regionId);
        if (region) return region;
      }

      // Fallback: API-Call
      try {
        return await api.get<Region>(`/v1/monitoring/regions/${regionId}`);
      } catch {
        return null;
      }
    },
    // Warte bis Hierarchie geladen ist, um Race-Condition zu vermeiden
    enabled: !!regionId && !isHierarchyLoading,
    refetchInterval: 30000,
    staleTime: 10000,
  });

  // Kombinierter Loading-State
  return {
    ...query,
    isLoading: isHierarchyLoading || query.isLoading,
  };
}

/**
 * Details eines einzelnen Verfahrens
 * Extrahiert die Daten aus der bereits geladenen Hierarchie.
 */
export function useVerfahrenDetails(verfahrenId: string) {
  const { data: hierarchy, isLoading: isHierarchyLoading } = useMonitoringHierarchy();

  const query = useQuery({
    queryKey: monitoringKeys.verfahrenDetail(verfahrenId),
    queryFn: async () => {
      // Aus der geladenen Hierarchie suchen
      if (hierarchy?.regions) {
        for (const region of hierarchy.regions) {
          const verfahren = region.verfahren.find((v) => v.id === verfahrenId);
          if (verfahren) return verfahren;
        }
      }

      // Fallback: API-Call
      try {
        return await api.get<Verfahren>(`/v1/monitoring/verfahren/${verfahrenId}`);
      } catch {
        return null;
      }
    },
    // Warte bis Hierarchie geladen ist, um Race-Condition zu vermeiden
    enabled: !!verfahrenId && !isHierarchyLoading,
    refetchInterval: 30000,
    staleTime: 10000,
  });

  // Kombinierter Loading-State
  return {
    ...query,
    isLoading: isHierarchyLoading || query.isLoading,
  };
}

/**
 * Details eines einzelnen Hosts mit Services und Metriken
 * Extrahiert die Daten aus der bereits geladenen Hierarchie,
 * um ID-Inkonsistenzen nach Cache-Ablauf zu vermeiden.
 */
export function useHostDetails(hostId: string) {
  const { data: hierarchy, isLoading: isHierarchyLoading } = useMonitoringHierarchy();

  const query = useQuery({
    queryKey: monitoringKeys.host(hostId),
    queryFn: async () => {
      // Zuerst aus der geladenen Hierarchie suchen
      if (hierarchy?.regions) {
        for (const region of hierarchy.regions) {
          for (const verfahren of region.verfahren) {
            const host = verfahren.hosts.find((h) => h.id === hostId);
            if (host) return host;
          }
        }
      }

      // Fallback: API-Call (nur wenn Hierarchie nicht verfügbar)
      try {
        return await api.get<Host>(`/v1/monitoring/hosts/${hostId}`);
      } catch {
        return null;
      }
    },
    // Warte bis Hierarchie geladen ist, um Race-Condition zu vermeiden
    enabled: !!hostId && !isHierarchyLoading,
    refetchInterval: 10000,
    staleTime: 5000,
  });

  // Kombinierter Loading-State: true wenn Hierarchie ODER Host-Query lädt
  return {
    ...query,
    isLoading: isHierarchyLoading || query.isLoading,
  };
}

// === Mutations ===

/**
 * Manueller Refresh eines Hosts
 * Triggert einen sofortigen Health-Check
 */
export function useRefreshHost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (hostId: string) =>
      api.post<Host>(`/v1/monitoring/hosts/${hostId}/refresh`),
    onSuccess: (_, hostId) => {
      // Invalidiere Host und übergeordnete Hierarchie
      queryClient.invalidateQueries({ queryKey: monitoringKeys.host(hostId) });
      queryClient.invalidateQueries({ queryKey: monitoringKeys.hierarchy() });
      queryClient.invalidateQueries({ queryKey: monitoringKeys.regions() });
      queryClient.invalidateQueries({ queryKey: monitoringKeys.verfahren() });
    },
  });
}

/**
 * Manueller Check eines einzelnen Services auf einem Host
 */
export function useCheckService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ hostId, serviceName }: { hostId: string; serviceName: string }) =>
      api.post<HostService>(`/v1/monitoring/hosts/${hostId}/services/${serviceName}/check`),
    onSuccess: (_, { hostId }) => {
      // Invalidiere Host-Details und Services
      queryClient.invalidateQueries({ queryKey: monitoringKeys.host(hostId) });
      queryClient.invalidateQueries({ queryKey: monitoringKeys.hostServices(hostId) });
      queryClient.invalidateQueries({ queryKey: monitoringKeys.hierarchy() });
    },
  });
}

// === Utility Hooks ===

/**
 * Hook für aggregierte Status-Statistiken
 */
export function useMonitoringStats() {
  return useQuery({
    queryKey: [...monitoringKeys.all, 'stats'] as const,
    queryFn: () =>
      api.get<{
        totalRegions: number;
        totalVerfahren: number;
        totalHosts: number;
        healthyHosts: number;
        warningHosts: number;
        offlineHosts: number;
      }>('/v1/monitoring/stats'),
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

/**
 * Hook für Hosts mit Filterung
 */
export function useHosts(filters?: {
  status?: 'online' | 'offline' | 'warning' | 'unknown';
  regionId?: string;
  verfahrenId?: string;
}) {
  return useQuery({
    queryKey: [...monitoringKeys.hosts(), filters] as const,
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      if (filters?.regionId) params.set('region_id', filters.regionId);
      if (filters?.verfahrenId) params.set('verfahren_id', filters.verfahrenId);

      const query = params.toString();
      const url = query ? `/v1/monitoring/hosts?${query}` : '/v1/monitoring/hosts';
      return api.get<{ items: Host[]; total: number }>(url);
    },
    refetchInterval: 30000,
  });
}
