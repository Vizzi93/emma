import { Settings as SettingsIcon } from 'lucide-react';

export function Settings() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Einstellungen</h1>
        <p className="text-gray-400 mt-1">
          Systemkonfiguration und Benutzereinstellungen
        </p>
      </div>

      <div className="card p-8 text-center">
        <SettingsIcon size={48} className="mx-auto text-gray-600 mb-4" />
        <p className="text-gray-400">Settings Panel</p>
        <p className="text-sm text-gray-500 mt-2">
          n8n Integration, Notifications, API Keys, User Management
        </p>
      </div>
    </div>
  );
}
