import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { User, UserSession, UserStats, CreateUserRequest, UpdateUserRequest } from '@/types/user';

export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...userKeys.lists(), filters] as const,
  detail: (id: string) => [...userKeys.all, 'detail', id] as const,
  sessions: (id: string) => [...userKeys.detail(id), 'sessions'] as const,
  stats: () => [...userKeys.all, 'stats'] as const,
};

export function useUserStats() {
  return useQuery({
    queryKey: userKeys.stats(),
    queryFn: () => api.get<UserStats>('/users/stats'),
  });
}

export function useUsers(filters?: {
  include_inactive?: boolean;
  role?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: userKeys.list(filters || {}),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.include_inactive) params.set('include_inactive', 'true');
      if (filters?.role) params.set('role', filters.role);
      if (filters?.search) params.set('search', filters.search);
      if (filters?.limit) params.set('limit', String(filters.limit));
      if (filters?.offset) params.set('offset', String(filters.offset));
      const query = params.toString();
      return api.get<{ items: User[]; total: number; limit: number; offset: number }>(
        query ? `/users?${query}` : '/users'
      );
    },
  });
}

export function useUser(userId: string) {
  return useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: () => api.get<User>(`/users/${userId}`),
    enabled: !!userId,
  });
}

export function useUserSessions(userId: string) {
  return useQuery({
    queryKey: userKeys.sessions(userId),
    queryFn: () => api.get<{ user_id: string; sessions: UserSession[]; total: number }>(`/users/${userId}/sessions`),
    enabled: !!userId,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateUserRequest) => api.post<User>('/users', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.stats() });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) => api.patch<User>(`/users/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: ({ id, newPassword }: { id: string; newPassword: string }) =>
      api.post(`/users/${id}/reset-password`, { new_password: newPassword }),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.invalidateQueries({ queryKey: userKeys.stats() });
    },
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => api.delete(`/users/${userId}/sessions`),
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: userKeys.sessions(userId) });
    },
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, sessionId }: { userId: string; sessionId: string }) =>
      api.delete(`/users/${userId}/sessions/${sessionId}`),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: userKeys.sessions(userId) });
    },
  });
}
