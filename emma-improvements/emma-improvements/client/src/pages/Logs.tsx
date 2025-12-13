import { ScrollText } from 'lucide-react';

export function Logs() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Logs</h1>
        <p className="text-gray-400 mt-1">
          Systemlogs und Events
        </p>
      </div>

      <div className="card p-8 text-center">
        <ScrollText size={48} className="mx-auto text-gray-600 mb-4" />
        <p className="text-gray-400">Log Viewer</p>
        <p className="text-sm text-gray-500 mt-2">
          Aggregierte Logs von allen Agents und Services
        </p>
      </div>
    </div>
  );
}
