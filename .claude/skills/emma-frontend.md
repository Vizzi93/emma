---
name: emma-frontend
description: eMMA frontend development with React, TypeScript, TailwindCSS. Use when working on client code.
globs:
  - "client/src/**/*.tsx"
  - "client/src/**/*.ts"
  - "client/src/**/*.css"
---

# eMMA Frontend Development

React 18 with TypeScript, TailwindCSS, Zustand, and React Query.

## Project Structure
```
client/src/
├── components/    # UI Components
├── pages/         # Page Components
├── hooks/         # React Query Hooks
├── stores/        # Zustand Stores
├── types/         # TypeScript Types
├── lib/           # Utilities
└── api/           # API client
```

## Component Pattern
```typescript
import { useState } from 'react';
import { useServices } from '@/hooks/useServices';
import { ServiceCard } from '@/components/ServiceCard';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface ServiceListProps {
  className?: string;
  onServiceSelect?: (id: number) => void;
}

export const ServiceList = ({ className, onServiceSelect }: ServiceListProps) => {
  const { data: services, isLoading, error } = useServices();
  const [filter, setFilter] = useState<string>('all');

  if (isLoading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error loading services</div>;
  }

  const filteredServices = services?.filter(s =>
    filter === 'all' || s.status === filter
  );

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex gap-2">
        <Button
          variant={filter === 'all' ? 'primary' : 'secondary'}
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button
          variant={filter === 'healthy' ? 'primary' : 'secondary'}
          onClick={() => setFilter('healthy')}
        >
          Healthy
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredServices?.map(service => (
          <ServiceCard
            key={service.id}
            service={service}
            onClick={() => onServiceSelect?.(service.id)}
          />
        ))}
      </div>
    </div>
  );
};
```

## React Query Hook Pattern
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Service, ServiceCreate } from '@/types/service';
import toast from 'react-hot-toast';

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: () => api.get<Service[]>('/v1/services'),
  });
};

export const useService = (id: number) => {
  return useQuery({
    queryKey: ['services', id],
    queryFn: () => api.get<Service>(`/v1/services/${id}`),
    enabled: !!id,
  });
};

export const useCreateService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ServiceCreate) =>
      api.post<Service>('/v1/services', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
      toast.success('Service created');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
};

export const useDeleteService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/v1/services/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
      toast.success('Service deleted');
    },
  });
};
```

## Zustand Store Pattern
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: (token, user) => set({
        token,
        user,
        isAuthenticated: true
      }),

      logout: () => set({
        token: null,
        user: null,
        isAuthenticated: false
      }),
    }),
    { name: 'auth-storage' }
  )
);
```

## API Client
```typescript
import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  get: <T>(url: string) => apiClient.get<T>(url).then(r => r.data),
  post: <T>(url: string, data: unknown) => apiClient.post<T>(url, data).then(r => r.data),
  put: <T>(url: string, data: unknown) => apiClient.put<T>(url, data).then(r => r.data),
  delete: (url: string) => apiClient.delete(url),
};
```

## TypeScript Types
```typescript
// types/service.ts
export interface Service {
  id: number;
  name: string;
  url: string;
  type: 'http' | 'tcp' | 'icmp' | 'dns';
  status: 'healthy' | 'unhealthy' | 'unknown';
  createdAt: string;
  updatedAt: string | null;
}

export interface ServiceCreate {
  name: string;
  url: string;
  type: Service['type'];
}

export interface ServiceUpdate extends Partial<ServiceCreate> {}
```

## Form with React Hook Form + Zod
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const serviceSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  url: z.string().url('Invalid URL'),
  type: z.enum(['http', 'tcp', 'icmp', 'dns']),
});

type ServiceFormData = z.infer<typeof serviceSchema>;

export const ServiceForm = ({ onSubmit }: { onSubmit: (data: ServiceFormData) => void }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<ServiceFormData>({
    resolver: zodResolver(serviceSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <input {...register('name')} placeholder="Service name" className="input" />
        {errors.name && <span className="text-red-500">{errors.name.message}</span>}
      </div>
      <div>
        <input {...register('url')} placeholder="URL" className="input" />
        {errors.url && <span className="text-red-500">{errors.url.message}</span>}
      </div>
      <select {...register('type')} className="select">
        <option value="http">HTTP</option>
        <option value="tcp">TCP</option>
        <option value="icmp">ICMP</option>
      </select>
      <button type="submit" className="btn btn-primary">Create</button>
    </form>
  );
};
```

## Commands
```bash
npm run dev        # Dev server
npm run build      # Production build
npm test           # Run tests
npm run lint       # ESLint
npm run type-check # TypeScript
npm run format     # Prettier
```
