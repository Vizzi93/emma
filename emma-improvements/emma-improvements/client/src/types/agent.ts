// Agent Types
export interface AgentModule {
  enabled: boolean;
  interval_seconds?: number;
  settings?: Record<string, unknown>;
}

export interface Agent {
  id: string;
  host_id: string;
  hostname: string;
  os: string;
  architecture: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  sampling_interval: number;
  tags: string[];
  modules: Record<string, AgentModule>;
  checks?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentRequest {
  host_id: string;
  hostname: string;
  os: string;
  architecture: string;
  sampling_interval: number;
  tags?: string[];
  modules?: Record<string, AgentModule>;
  checks?: Record<string, unknown>;
}

export interface ProvisionAgentResponse {
  agent_id: string;
  token: string;
  expires_at: string;
}

// Service Types
export interface Service {
  id: string;
  name: string;
  type: 'docker' | 'http' | 'tcp' | 'ssl' | 'dns';
  status: 'up' | 'down' | 'degraded' | 'unknown';
  url?: string;
  last_check: string;
  response_time_ms?: number;
  metadata?: Record<string, unknown>;
}

// Alert Types
export interface Alert {
  id: string;
  agent_id?: string;
  service_id?: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  acknowledged: boolean;
  created_at: string;
  resolved_at?: string;
}

// Log Types
export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  source: string;
  message: string;
  metadata?: Record<string, unknown>;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  errors?: Array<{
    field: string;
    message: string;
    type: string;
  }>;
}
