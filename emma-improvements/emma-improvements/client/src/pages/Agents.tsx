import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Server,
  Plus,
  Search,
  Filter,
  MoreVertical,
  ExternalLink,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';

import { api } from '@/lib/api';
import { Agent } from '@/types/agent';

// Mock data - später durch API ersetzen
const mockAgents: Agent[] = [
  {
    id: '1',
    host_id: 'host-prod-web-01',
    hostname: 'prod-web-01',
    os: 'linux',
    architecture: 'x86_64',
    status: 'healthy',
    sampling_interval: 30,
    tags: ['production', 'web'],
    modules: { cpu: { enabled: true }, memory: { enabled: true } },
    created_at: '2024-03-15T10:00:00Z',
    updated_at: '2024-03-20T14:30:00Z',
  },
  {
    id: '2',
    host_id: 'host-prod-db-01',
    hostname: 'prod-db-01',
    os: 'linux',
    architecture: 'x86_64',
    status: 'warning',
    sampling_interval: 15,
    tags: ['production', 'database'],
    modules: { cpu: { enabled: true }, disk: { enabled: true } },
    created_at: '2024-03-10T08:00:00Z',
    updated_at: '2024-03-20T14:25:00Z',
  },
  {
    id: '3',
    host_id: 'host-staging-api-01',
    hostname: 'staging-api-01',
    os: 'linux',
    architecture: 'arm64',
    status: 'healthy',
    sampling_interval: 60,
    tags: ['staging', 'api'],
    modules: { cpu: { enabled: true } },
    created_at: '2024-03-18T12:00:00Z',
    updated_at: '2024-03-20T14:20:00Z',
  },
];

export function Agents() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // API Query - nutzt erstmal Mock-Daten
  // const { data: agents, isLoading } = useQuery({
  //   queryKey: ['agents'],
  //   queryFn: () => api.get<Agent[]>('/agents'),
  // });

  const agents = mockAgents;
  const isLoading = false;

  const filteredAgents = agents?.filter((agent) => {
    const matchesSearch =
      agent.hostname.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.host_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <span className="badge-success">Healthy</span>;
      case 'warning':
        return <span className="badge-warning">Warning</span>;
      case 'critical':
        return <span className="badge-error">Critical</span>;
      default:
        return <span className="badge-info">Unknown</span>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Agents</h1>
          <p className="text-gray-400 mt-1">
            Verwalte und überwache alle registrierten Agents
          </p>
        </div>
        <button className="btn-primary">
          <Plus size={18} />
          Agent hinzufügen
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Suche nach Hostname, Host-ID oder Tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-40"
            >
              <option value="all">Alle Status</option>
              <option value="healthy">Healthy</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Refresh */}
          <button className="btn-ghost">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Agents Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">
            <RefreshCw size={24} className="mx-auto animate-spin mb-2" />
            Lade Agents...
          </div>
        ) : filteredAgents && filteredAgents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Status</th>
                  <th>OS / Arch</th>
                  <th>Tags</th>
                  <th>Interval</th>
                  <th>Last Update</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredAgents.map((agent) => (
                  <tr key={agent.id}>
                    <td>
                      <Link
                        to={`/agents/${agent.id}`}
                        className="flex items-center gap-3 group"
                      >
                        <div className="p-2 rounded-lg bg-gray-800 group-hover:bg-emma-600/20 transition-colors">
                          <Server size={18} className="text-gray-400 group-hover:text-emma-400" />
                        </div>
                        <div>
                          <p className="font-medium text-white group-hover:text-emma-400 transition-colors">
                            {agent.hostname}
                          </p>
                          <p className="text-xs text-gray-500">{agent.host_id}</p>
                        </div>
                      </Link>
                    </td>
                    <td>{getStatusBadge(agent.status)}</td>
                    <td>
                      <span className="text-gray-300">{agent.os}</span>
                      <span className="text-gray-500"> / {agent.architecture}</span>
                    </td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {agent.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 text-xs rounded bg-gray-800 text-gray-400"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="text-gray-400">{agent.sampling_interval}s</td>
                    <td className="text-gray-400 text-sm">
                      {formatDistanceToNow(new Date(agent.updated_at), {
                        addSuffix: true,
                        locale: de,
                      })}
                    </td>
                    <td>
                      <div className="flex items-center gap-1">
                        <Link
                          to={`/agents/${agent.id}`}
                          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                        >
                          <ExternalLink size={16} />
                        </Link>
                        <button className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center">
            <Server size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Agents gefunden</p>
            <p className="text-sm text-gray-500 mt-1">
              {searchQuery || statusFilter !== 'all'
                ? 'Versuche andere Filteroptionen'
                : 'Füge deinen ersten Agent hinzu'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
