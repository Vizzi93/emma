import { createContext, useContext, ReactNode, useCallback, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useWebSocket } from '@/hooks/useWebSocket';

interface WebSocketContextValue {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  isConnected: boolean;
  lastEvent: unknown;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  // Use ref to track shown toasts (avoids dependency loop)
  const toastShownRef = useRef<Record<string, boolean>>({});
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Cleanup all timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutsRef.current.forEach((timeout) => clearTimeout(timeout));
      timeoutsRef.current.clear();
    };
  }, []);

  const handleStatusChange = useCallback(
    (serviceId: string, oldStatus: string, newStatus: string) => {
      // Show toast for status changes
      const toastKey = `${serviceId}-${newStatus}`;
      if (toastShownRef.current[toastKey]) return;

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

      toastShownRef.current[toastKey] = true;

      // Clear any existing timeout for this key
      const existingTimeout = timeoutsRef.current.get(toastKey);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // Reset toast shown after 30 seconds with cleanup tracking
      const timeoutId = setTimeout(() => {
        delete toastShownRef.current[toastKey];
        timeoutsRef.current.delete(toastKey);
      }, 30000);

      timeoutsRef.current.set(toastKey, timeoutId);
    },
    []
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
