// Docker Types

export type ContainerState = 
  | 'created'
  | 'restarting'
  | 'running'
  | 'removing'
  | 'paused'
  | 'exited'
  | 'dead';

export interface ContainerPortMapping {
  host_ip: string;
  host_port: string;
}

export interface Container {
  id: string;
  short_id: string;
  name: string;
  image: string;
  status: string;
  state: ContainerState;
  created: string;
  started_at: string | null;
  ports: Record<string, ContainerPortMapping[]>;
  labels: Record<string, string>;
  health_status: string | null;
}

export interface ContainerStats {
  container_id: string;
  container_name: string;
  cpu_percent: number;
  memory_usage: number;
  memory_limit: number;
  memory_percent: number;
  network_rx: number;
  network_tx: number;
  block_read: number;
  block_write: number;
  pids: number;
  timestamp: string;
}

export interface DockerInfo {
  containers: number;
  containers_running: number;
  containers_paused: number;
  containers_stopped: number;
  images: number;
  docker_version: string;
  os: string;
  architecture: string;
  cpus: number;
  memory: number;
  storage_driver: string;
}

export interface ContainerLogs {
  container_id: string;
  logs: string[];
  total_lines: number;
}
