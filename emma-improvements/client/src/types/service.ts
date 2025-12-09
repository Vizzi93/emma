// Service Types
export type ServiceType = 'http' | 'https' | 'tcp' | 'ssl' | 'dns' | 'ping';
export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | 'paused';

export interface ServiceConfig {
  // HTTP/HTTPS specific
  method?: string;
  expected_status?: number;
  expected_body?: string;
  headers?: Record<string, string>;
  verify_ssl?: boolean;
  follow_redirects?: boolean;

  // SSL specific
  warn_days?: number;

  // DNS specific
  expected_ip?: string;
  record_type?: string;

  // Ping specific
  count?: number;
}

export interface Service {
  id: string;
  name: string;
  description: string | null;
  type: ServiceType;
  target: string;
  config: ServiceConfig;
  interval_seconds: number;
  timeout_seconds: number;
  status: ServiceStatus;
  is_active: boolean;
  last_check_at: string | null;
  last_response_time_ms: number | null;
  uptime_percentage: number;
  consecutive_failures: number;
  tags: string[];
  group_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckResult {
  id: string;
  service_id: string;
  is_healthy: boolean;
  status_code: number | null;
  response_time_ms: number | null;
  message: string | null;
  error: string | null;
  metadata: Record<string, unknown>;
  checked_at: string;
}

export interface ServiceWithHistory extends Service {
  recent_checks: CheckResult[];
}

export interface CreateServiceRequest {
  name: string;
  description?: string;
  type: ServiceType;
  target: string;
  config?: ServiceConfig;
  interval_seconds?: number;
  timeout_seconds?: number;
  tags?: string[];
  group_name?: string;
}

export interface UpdateServiceRequest {
  name?: string;
  description?: string;
  target?: string;
  config?: ServiceConfig;
  interval_seconds?: number;
  timeout_seconds?: number;
  tags?: string[];
  group_name?: string;
  is_active?: boolean;
}

export interface DashboardStats {
  total_services: number;
  status_counts: Record<ServiceStatus, number>;
  services_due: number;
  avg_response_time_ms: number | null;
}

export interface UptimeDataPoint {
  timestamp: string;
  is_healthy: boolean;
  response_time_ms: number | null;
}

export interface ServiceUptimeData {
  service_id: string;
  service_name: string;
  uptime_percentage: number;
  data_points: UptimeDataPoint[];
}
