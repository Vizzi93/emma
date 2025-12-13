import { createContext, useContext, ReactNode, useCallback, useState } from 'react';
import toast from 'react-hot-toast';
import { useWebSocket } from '@/hooks/useWebSocket';

interface WebSocketContextValue {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  isConnected: boolean;
  lastEvent: unknown;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [toastShown, setToastShown] = useState<Record<string, boolean>>({});

  const handleStatusChange = useCallback(
    (serviceId: string, oldStatus: string, newStatus: string) => {
      // Show toast for status changes
      const toastKey = `${serviceId}-${newStatus}`;
      if (toastShown[toastKey]) return;

      if (newStatus === 'unhealthy') {
        toast.error(`Service ist jetzt unhealthy`, {
          duration: 5000,
          icon: '🔴',
        });
      } else if (newStatus === 'healthy' && oldStatus !== 'unknown') {
        toast.success(`Service ist wieder healthy`, {
          duration: 3000,
          icon: '🟢',
        });
      } else if (newStatus === 'degraded') {
        toast(`Service ist degraded`, {
          duration: 4000,
          icon: '🟡',
        });
      }

      setToastShown((prev) => ({ ...prev, [toastKey]: true }));
      
      // Reset toast shown after 30 seconds
      setTimeout(() => {
        setToastShown((prev) => {
          const next = { ...prev };
          delete next[toastKey];
          return next;
        });
      }, 30000);
    },
    [toastShown]
  );

  const { status, isConnected, lastEvent } = useWebSocket({
    onStatusChange: handleStatusChange,
    onCheckComplete: (serviceId, isHealthy) => {
      // Could show subtle indicator for check completions
      console.log(`[WS] Check completed: ${serviceId} - ${isHealthy ? 'healthy' : 'unhealthy'}`);
    },
  });

  return (
    <WebSocketContext.Provider value={{ status, isConnected, lastEvent }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
}
