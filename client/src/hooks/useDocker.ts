import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Container, ContainerStats, DockerInfo, ContainerLogs } from '@/types/docker';

export const dockerKeys = {
  all: ['docker'] as const,
  info: () => [...dockerKeys.all, 'info'] as const,
  containers: () => [...dockerKeys.all, 'containers'] as const,
  container: (id: string) => [...dockerKeys.containers(), id] as const,
  stats: (id: string) => [...dockerKeys.container(id), 'stats'] as const,
  logs: (id: string) => [...dockerKeys.container(id), 'logs'] as const,
};

export function useDockerInfo() {
  return useQuery({
    queryKey: dockerKeys.info(),
    queryFn: () => api.get<DockerInfo>('/v1/docker/info'),
    refetchInterval: 30000,
    retry: false,
  });
}

export function useContainers(filters?: { all?: boolean; status?: string }) {
  return useQuery({
    queryKey: dockerKeys.containers(),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.all !== undefined) params.set('all', String(filters.all));
      if (filters?.status) params.set('status', filters.status);
      const query = params.toString();
      return api.get<{ items: Container[]; total: number }>(query ? `/v1/docker/containers?${query}` : '/v1/docker/containers');
    },
    refetchInterval: 10000,
    retry: false,
  });
}

export function useContainer(containerId: string) {
  return useQuery({
    queryKey: dockerKeys.container(containerId),
    queryFn: () => api.get<Container>(`/v1/docker/containers/${containerId}`),
    enabled: !!containerId,
    refetchInterval: 5000,
  });
}

export function useContainerStats(containerId: string) {
  return useQuery({
    queryKey: dockerKeys.stats(containerId),
    queryFn: () => api.get<ContainerStats>(`/v1/docker/containers/${containerId}/stats`),
    enabled: !!containerId,
    refetchInterval: 3000,
  });
}

export function useContainerLogs(containerId: string, tail: number = 100) {
  return useQuery({
    queryKey: dockerKeys.logs(containerId),
    queryFn: () => api.get<ContainerLogs>(`/v1/docker/containers/${containerId}/logs?tail=${tail}`),
    enabled: !!containerId,
  });
}

export function useStartContainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (containerId: string) => api.post(`/v1/docker/containers/${containerId}/start`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dockerKeys.containers() });
      queryClient.invalidateQueries({ queryKey: dockerKeys.info() });
    },
  });
}

export function useStopContainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ containerId, timeout = 10 }: { containerId: string; timeout?: number }) =>
      api.post(`/v1/docker/containers/${containerId}/stop?timeout=${timeout}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dockerKeys.containers() });
      queryClient.invalidateQueries({ queryKey: dockerKeys.info() });
    },
  });
}

export function useRestartContainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ containerId, timeout = 10 }: { containerId: string; timeout?: number }) =>
      api.post(`/v1/docker/containers/${containerId}/restart?timeout=${timeout}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: dockerKeys.containers() }),
  });
}

export function useRemoveContainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ containerId, force = false }: { containerId: string; force?: boolean }) =>
      api.delete(`/v1/docker/containers/${containerId}?force=${force}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dockerKeys.containers() });
      queryClient.invalidateQueries({ queryKey: dockerKeys.info() });
    },
  });
}
