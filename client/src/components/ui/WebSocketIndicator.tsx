import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useWebSocketContext } from '@/providers/WebSocketProvider';

export function WebSocketIndicator() {
  const { status, isConnected } = useWebSocketContext();

  if (status === 'connecting') {
    return (
      <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-yellow-900/30 text-yellow-400 text-xs">
        <Loader2 size={12} className="animate-spin" />
        <span className="hidden sm:inline">Verbinde...</span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-green-900/30 text-green-400 text-xs">
        <Wifi size={12} />
        <span className="hidden sm:inline">Live</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-red-900/30 text-red-400 text-xs">
      <WifiOff size={12} />
      <span className="hidden sm:inline">Offline</span>
    </div>
  );
}
