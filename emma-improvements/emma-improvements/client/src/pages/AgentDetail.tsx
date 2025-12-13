import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Server } from 'lucide-react';

export function AgentDetail() {
  const { agentId } = useParams();

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-4">
        <Link
          to="/agents"
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Details</h1>
          <p className="text-gray-400">ID: {agentId}</p>
        </div>
      </div>

      <div className="card p-8 text-center">
        <Server size={48} className="mx-auto text-gray-600 mb-4" />
        <p className="text-gray-400">Agent Detail View</p>
        <p className="text-sm text-gray-500 mt-2">
          Hier werden Metriken, Logs und Konfiguration des Agents angezeigt
        </p>
      </div>
    </div>
  );
}
