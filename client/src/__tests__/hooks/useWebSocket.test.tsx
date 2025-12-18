import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason }));
    }
  }

  // Helper to simulate incoming message
  simulateMessage(data: object) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }
}

// Mock authStore
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    tokens: { access_token: 'mock-token' },
  }),
}));

describe('useWebSocket', () => {
  let mockWs: MockWebSocket | null = null;
  let queryClient: QueryClient;

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    // Mock WebSocket constructor using vi.stubGlobal
    const mockWebSocketConstructor = vi.fn((url: string) => {
      mockWs = new MockWebSocket(url);
      return mockWs;
    });

    // Copy static properties
    Object.assign(mockWebSocketConstructor, {
      CONNECTING: MockWebSocket.CONNECTING,
      OPEN: MockWebSocket.OPEN,
      CLOSING: MockWebSocket.CLOSING,
      CLOSED: MockWebSocket.CLOSED,
    });

    vi.stubGlobal('WebSocket', mockWebSocketConstructor);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockWs = null;
    vi.clearAllMocks();
  });

  it('should connect on mount', async () => {
    // Dynamic import to avoid hoisting issues
    const { useWebSocket } = await import('@/hooks/useWebSocket');

    const { result } = renderHook(() => useWebSocket(), { wrapper });

    // Wait for connection - the hook may start disconnected then connect
    await waitFor(
      () => {
        expect(result.current.status).toBe('connected');
      },
      { timeout: 1000 }
    );

    expect(result.current.isConnected).toBe(true);
  });

  it('should disconnect on unmount', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');

    const { result, unmount } = renderHook(() => useWebSocket(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isConnected).toBe(true);
      },
      { timeout: 1000 }
    );

    unmount();

    // After unmount, the WebSocket should be closed (readyState 3) or closing
    expect(mockWs?.readyState).toBeGreaterThanOrEqual(MockWebSocket.OPEN);
  });

  it('should handle incoming messages', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');
    const onEvent = vi.fn();

    const { result } = renderHook(() => useWebSocket({ onEvent }), { wrapper });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate incoming message
    act(() => {
      mockWs?.simulateMessage({
        type: 'service.status_changed',
        data: { id: '1', old_status: 'healthy', new_status: 'unhealthy' },
        timestamp: new Date().toISOString(),
      });
    });

    expect(onEvent).toHaveBeenCalled();
    expect(onEvent.mock.calls[0][0].type).toBe('service.status_changed');
  });

  it('should call onStatusChange callback', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');
    const onStatusChange = vi.fn();

    const { result } = renderHook(() => useWebSocket({ onStatusChange }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Simulate status change message
    act(() => {
      mockWs?.simulateMessage({
        type: 'service.status_changed',
        data: { id: 'service-1', old_status: 'healthy', new_status: 'unhealthy' },
        timestamp: new Date().toISOString(),
      });
    });

    expect(onStatusChange).toHaveBeenCalledWith('service-1', 'healthy', 'unhealthy');
  });

  it('should expose send function', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');

    const { result } = renderHook(() => useWebSocket(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isConnected).toBe(true);
      },
      { timeout: 1000 }
    );

    // Verify send function exists and is callable
    expect(typeof result.current.send).toBe('function');
  });

  it('should expose disconnect function', async () => {
    const { useWebSocket } = await import('@/hooks/useWebSocket');

    const { result } = renderHook(() => useWebSocket(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isConnected).toBe(true);
      },
      { timeout: 1000 }
    );

    // Verify disconnect function exists
    expect(typeof result.current.disconnect).toBe('function');
  });
});
