import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { serviceKeys } from '@/hooks/useServices';

// Event types from backend
type EventType =
  | 'connected'
  | 'ping'
  | 'pong'
  | 'service.created'
  | 'service.updated'
  | 'service.deleted'
  | 'service.status_changed'
  | 'service.check_completed'
  | 'alert.triggered'
  | 'alert.resolved';

interface WebSocketEvent {
  type: EventType;
  data: Record<string, unknown>;
  timestamp: string;
}

interface UseWebSocketOptions {
  onEvent?: (event: WebSocketEvent) => void;
  onStatusChange?: (serviceId: string, oldStatus: string, newStatus: string) => void;
  onCheckComplete?: (serviceId: string, isHealthy: boolean) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onEvent,
    onStatusChange,
    onCheckComplete,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const queryClient = useQueryClient();
  const { tokens } = useAuthStore();

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || `${protocol}//${window.location.host}`;
    const baseUrl = `${host}/v1/ws`;
    
    if (tokens?.access_token) {
      return `${baseUrl}?token=${tokens.access_token}`;
    }
    return baseUrl;
  }, [tokens?.access_token]);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const wsEvent: WebSocketEvent = JSON.parse(event.data);
        setLastEvent(wsEvent);

        // Call custom event handler
        onEvent?.(wsEvent);

        // Handle specific event types
        switch (wsEvent.type) {
          case 'service.status_changed': {
            const { id, old_status, new_status } = wsEvent.data as {
              id: string;
              old_status: string;
              new_status: string;
            };
            onStatusChange?.(id, old_status, new_status);
            // Invalidate service queries to refresh data
            queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
            queryClient.invalidateQueries({ queryKey: serviceKeys.detail(id) });
            queryClient.invalidateQueries({ queryKey: serviceKeys.stats() });
            break;
          }

          case 'service.check_completed': {
            const { service_id, is_healthy } = wsEvent.data as {
              service_id: string;
              is_healthy: boolean;
            };
            onCheckComplete?.(service_id, is_healthy);
            // Update specific service data
            queryClient.invalidateQueries({ queryKey: serviceKeys.detail(service_id) });
            queryClient.invalidateQueries({ queryKey: serviceKeys.history(service_id) });
            break;
          }

          case 'service.created':
          case 'service.deleted':
            queryClient.invalidateQueries({ queryKey: serviceKeys.lists() });
            queryClient.invalidateQueries({ queryKey: serviceKeys.stats() });
            break;

          case 'alert.triggered':
          case 'alert.resolved':
            // Could add alert handling here
            break;

          case 'ping':
            // Send pong response
            wsRef.current?.send(JSON.stringify({ type: 'pong' }));
            break;
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    },
    [onEvent, onStatusChange, onCheckComplete, queryClient]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');
    const url = getWebSocketUrl();
    
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        console.log('[WebSocket] Connected');

        // Subscribe to channels
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'services' }));
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'alerts' }));
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        setStatus('disconnected');
        console.log('[WebSocket] Disconnected:', event.code, event.reason);

        // Attempt reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(
            `[WebSocket] Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          );
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setStatus('error');
        console.error('[WebSocket] Error:', error);
      };

      wsRef.current = ws;
    } catch (error) {
      setStatus('error');
      console.error('[WebSocket] Failed to connect:', error);
    }
  }, [getWebSocketUrl, handleMessage, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Reconnect when token changes
  useEffect(() => {
    if (tokens?.access_token) {
      disconnect();
      connect();
    }
  }, [tokens?.access_token, connect, disconnect]);

  return {
    status,
    lastEvent,
    connect,
    disconnect,
    send,
    isConnected: status === 'connected',
  };
}
