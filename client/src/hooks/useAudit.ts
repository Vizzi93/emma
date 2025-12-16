import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AuditLog, AuditStats } from '@/types/audit';

export const auditKeys = {
  all: ['audit'] as const,
  lists: () => [...auditKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...auditKeys.lists(), filters] as const,
  stats: (days: number) => [...auditKeys.all, 'stats', days] as const,
  userActivity: (userId: string) => [...auditKeys.all, 'user', userId] as const,
  resourceHistory: (type: string, id: string) => [...auditKeys.all, 'resource', type, id] as const,
};

export function useAuditStats(days: number = 7) {
  return useQuery({
    queryKey: auditKeys.stats(days),
    queryFn: () => api.get<AuditStats>(`/v1/audit/stats?days=${days}`),
  });
}

export function useAuditLogs(filters?: {
  action?: string;
  resource_type?: string;
  user_id?: string;
  success?: boolean;
  since?: string;
  until?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: auditKeys.list(filters || {}),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.set('action', filters.action);
      if (filters?.resource_type) params.set('resource_type', filters.resource_type);
      if (filters?.user_id) params.set('user_id', filters.user_id);
      if (filters?.success !== undefined) params.set('success', String(filters.success));
      if (filters?.since) params.set('since', filters.since);
      if (filters?.until) params.set('until', filters.until);
      if (filters?.search) params.set('search', filters.search);
      if (filters?.limit) params.set('limit', String(filters.limit));
      if (filters?.offset) params.set('offset', String(filters.offset));
      const query = params.toString();
      return api.get<{ items: AuditLog[]; total: number; limit: number; offset: number }>(
        query ? `/v1/audit?${query}` : '/v1/audit'
      );
    },
    refetchInterval: 30000,
  });
}

export function useUserActivity(userId: string, days: number = 30) {
  return useQuery({
    queryKey: auditKeys.userActivity(userId),
    queryFn: () => api.get<AuditLog[]>(`/v1/audit/user/${userId}?days=${days}`),
    enabled: !!userId,
  });
}

export function useResourceHistory(resourceType: string, resourceId: string) {
  return useQuery({
    queryKey: auditKeys.resourceHistory(resourceType, resourceId),
    queryFn: () => api.get<AuditLog[]>(`/v1/audit/resource/${resourceType}/${resourceId}`),
    enabled: !!resourceType && !!resourceId,
  });
}

export async function exportAuditLogs(filters?: {
  action?: string;
  resource_type?: string;
  user_id?: string;
  success?: boolean;
  since?: string;
  until?: string;
  format?: 'json' | 'csv';
}): Promise<Blob> {
  const params = new URLSearchParams();
  if (filters?.action) params.set('action', filters.action);
  if (filters?.resource_type) params.set('resource_type', filters.resource_type);
  if (filters?.user_id) params.set('user_id', filters.user_id);
  if (filters?.success !== undefined) params.set('success', String(filters.success));
  if (filters?.since) params.set('since', filters.since);
  if (filters?.until) params.set('until', filters.until);
  params.set('format', filters?.format || 'json');

  const query = params.toString();
  const response = await fetch(`/v1/audit/export?${query}`);
  return response.blob();
}
