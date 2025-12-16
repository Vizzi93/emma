import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Server,
  Plus,
  Search,
  Filter,
  ExternalLink,
  Trash2,
  RefreshCw,
  X,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { useAgents, useCreateAgent, useDeleteAgent } from '@/hooks/useAgents';
import type { Agent, CreateAgentRequest } from '@/types/agent';

// Create Agent Modal
function CreateAgentModal({ onClose }: { onClose: () => void }) {
  const createAgent = useCreateAgent();
  const [form, setForm] = useState<CreateAgentRequest>({
    host_id: '',
    hostname: '',
    os: 'linux',
    architecture: 'x86_64',
    sampling_interval: 30,
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createAgent.mutateAsync(form);
      toast.success('Agent erfolgreich erstellt');
      onClose();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Fehler beim Erstellen des Agents');
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !form.tags?.includes(tagInput.trim())) {
      setForm({ ...form, tags: [...(form.tags || []), tagInput.trim()] });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setForm({ ...form, tags: form.tags?.filter((t) => t !== tag) || [] });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="card p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Neuer Agent</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Host-ID *</label>
              <input
                type="text"
                required
                value={form.host_id}
                onChange={(e) => setForm({ ...form, host_id: e.target.value })}
                className="input"
                placeholder="host-prod-web-01"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Hostname *</label>
              <input
                type="text"
                required
                value={form.hostname}
                onChange={(e) => setForm({ ...form, hostname: e.target.value })}
                className="input"
                placeholder="prod-web-01"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Betriebssystem</label>
              <select
                value={form.os}
                onChange={(e) => setForm({ ...form, os: e.target.value })}
                className="input"
              >
                <option value="linux">Linux</option>
                <option value="windows">Windows</option>
                <option value="macos">macOS</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Architektur</label>
              <select
                value={form.architecture}
                onChange={(e) => setForm({ ...form, architecture: e.target.value })}
                className="input"
              >
                <option value="x86_64">x86_64</option>
                <option value="arm64">arm64</option>
                <option value="i386">i386</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Interval (s)</label>
              <input
                type="number"
                min={5}
                max={3600}
                value={form.sampling_interval}
                onChange={(e) => setForm({ ...form, sampling_interval: parseInt(e.target.value) || 30 })}
                className="input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Tags</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                className="input flex-1"
                placeholder="Tag eingeben..."
              />
              <button type="button" onClick={addTag} className="btn-ghost">
                Hinzufügen
              </button>
            </div>
            {form.tags && form.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {form.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 text-sm bg-gray-800 text-gray-300 rounded flex items-center gap-1"
                  >
                    {tag}
                    <button type="button" onClick={() => removeTag(tag)} className="text-gray-500 hover:text-red-400">
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2 pt-4 border-t border-gray-700">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">
              Abbrechen
            </button>
            <button type="submit" disabled={createAgent.isPending} className="btn-primary flex-1">
              {createAgent.isPending ? 'Erstelle...' : 'Agent erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function Agents() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // API Queries
  const { data: agentsData, isLoading, refetch } = useAgents({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    search: searchQuery || undefined,
  });
  const deleteAgent = useDeleteAgent();

  const agents = agentsData?.items || [];

  const handleDelete = async (agent: Agent) => {
    if (!confirm(`Agent "${agent.hostname}" wirklich löschen?`)) return;
    try {
      await deleteAgent.mutateAsync(agent.id);
      toast.success('Agent gelöscht');
    } catch {
      toast.error('Fehler beim Löschen');
    }
  };

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
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
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
          <button onClick={() => refetch()} className="btn-ghost">
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
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
        ) : agents.length > 0 ? (
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
                {agents.map((agent) => (
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
                        <button
                          onClick={() => handleDelete(agent)}
                          className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                        >
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

      {/* Create Modal */}
      {showCreateModal && <CreateAgentModal onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}
