import { Link } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

export function NotFound() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-900/30 text-red-400 mb-6">
          <AlertCircle size={32} />
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">404</h1>
        <p className="text-xl text-gray-400 mb-8">Seite nicht gefunden</p>
        <Link to="/dashboard" className="btn-primary">
          <Home size={18} />
          Zurück zum Dashboard
        </Link>
      </div>
    </div>
  );
}
