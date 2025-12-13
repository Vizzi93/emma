import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  Service,
  ServiceWithHistory,
  CreateServiceRequest,
  UpdateServiceRequest,
  CheckResult,
  DashboardStats,
  ServiceUptimeData,
} from '@/types/service';

// Query Keys
export const serviceKeys = {
  all: ['services'] as const,
  lists: () => [...serviceKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...serviceKeys.lists(), filters] as const,
  details: () => [...serviceKeys.all, 'detail'] as const,
  detail: (id: string) => [...serviceKeys.details(), id] as const,
  history: (id: string) => [...serviceKeys.detail(id), 'history'] as const,
  uptime: (id: string) => [...serviceKeys.detail(id), 'uptime'] as const,
  stats: () => [...serviceKeys.all, 'stats'] as const,
};

// === Queries ===

export function useServices(filters?: {
  is_active?: boolean;
  status?: string;
  type?: string;
  group_name?: string;
}) {
  return useQuery({
    queryKey: serviceKeys.list(filters || {}),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
      if (filters?.status) params.set('status', filters.status);
      if (filters?.type) params.set('type', filters.type);
      if (filters?.group_name) params.set('group_name', filters.group_name);

      const query = params.toString();
      const url = query ? `/services?${query}` : '/services';
      return api.get<{ items: Service[]; total: number }>(url);
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useService(serviceId: string) {
  return useQuery({
    queryKey: serviceKeys.detail(serviceId),
    queryFn: () => api.get<ServiceWithHistory>(`/services/${serviceId}`),
    enabled: !!serviceId,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}

export function useServiceHistory(serviceId: string, hours: number = 24) {
  return useQuery({
    queryKey: serviceKeys.history(serviceId),
    queryFn: () => api.get<CheckResult[]>(`/services/${serviceId}/history?hours=${hours}`),
    enabled: !!serviceId,
    refetchInterval: 30000,
  });
}

export function useServiceUptime(serviceId: string, hours: number = 24) {
  return useQuery({
    queryKey: serviceKeys.uptime(serviceId),
    queryFn: () => api.get<ServiceUptimeData>(`/services/${serviceId}/uptime?hours=${hours}`),
    enabled: !!serviceId,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: serviceKeys.stats(),
    queryFn: () => api.get<DashboardStats>('/services/stats'),
    refetchInterval: 30000,
  });
}

// === Mutations ===

export function useCreateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateServiceRequest) => api.post<Service>('/services', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: serviceKeys.stats() });
    },
  });
}

export function useUpdateService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateServiceRequest }) =>
      api.patch<Service>(`/services/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: serviceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
    },
  });
}

export function useDeleteService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/services/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: serviceKeys.stats() });
    },
  });
}

export function useToggleService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.post<Service>(`/services/${id}/toggle?is_active=${is_active}`),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: serviceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: serviceKeys.stats() });
    },
  });
}

export function useRunCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.post<CheckResult>(`/services/${id}/check`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: serviceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: serviceKeys.history(id) });
      queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
    },
  });
}
