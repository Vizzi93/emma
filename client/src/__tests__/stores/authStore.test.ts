import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useAuthStore } from '@/stores/authStore';
import { server } from '@/test/setup';
import { HttpResponse, http } from 'msw';

// Mock user response
const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'viewer',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  last_login_at: null,
};

const mockTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  expires_in: 1800,
};

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      rememberMe: false,
    });

    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  describe('login', () => {
    it('should login successfully', async () => {
      server.use(
        http.post('/api/v1/auth/login', () => {
          return HttpResponse.json({
            user: mockUser,
            tokens: mockTokens,
          });
        })
      );

      const { login } = useAuthStore.getState();

      await login('test@example.com', 'password123');

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
      expect(state.tokens).toEqual(mockTokens);
      expect(state.error).toBeNull();
    });

    it('should handle login error', async () => {
      server.use(
        http.post('/api/v1/auth/login', () => {
          return HttpResponse.json(
            { detail: 'Invalid credentials' },
            { status: 401 }
          );
        })
      );

      const { login } = useAuthStore.getState();

      await expect(login('test@example.com', 'wrongpassword')).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.error).toBe('Login fehlgeschlagen');
    });

    it('should set loading state during login', async () => {
      server.use(
        http.post('/api/v1/auth/login', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json({
            user: mockUser,
            tokens: mockTokens,
          });
        })
      );

      const { login } = useAuthStore.getState();
      const loginPromise = login('test@example.com', 'password123');

      // Check loading state
      expect(useAuthStore.getState().isLoading).toBe(true);

      await loginPromise;

      // Check loading is false after completion
      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: mockUser,
        tokens: mockTokens,
        isAuthenticated: true,
      });

      server.use(
        http.post('/api/v1/auth/logout', () => {
          return HttpResponse.json({ message: 'Logged out' });
        })
      );

      const { logout } = useAuthStore.getState();

      await logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.tokens).toBeNull();
    });

    it('should logout even if API call fails', async () => {
      useAuthStore.setState({
        user: mockUser,
        tokens: mockTokens,
        isAuthenticated: true,
      });

      server.use(
        http.post('/api/v1/auth/logout', () => {
          return HttpResponse.json({ detail: 'Error' }, { status: 500 });
        })
      );

      const { logout } = useAuthStore.getState();

      await logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      useAuthStore.setState({
        tokens: mockTokens,
        isAuthenticated: true,
      });

      const newAccessToken = 'new-access-token';

      server.use(
        http.post('/api/v1/auth/refresh', () => {
          return HttpResponse.json({
            access_token: newAccessToken,
            expires_in: 1800,
          });
        })
      );

      const { refreshToken } = useAuthStore.getState();

      const result = await refreshToken();

      expect(result).toBe(true);
      expect(useAuthStore.getState().tokens?.access_token).toBe(newAccessToken);
    });

    it('should return false when no refresh token', async () => {
      useAuthStore.setState({
        tokens: null,
        isAuthenticated: false,
      });

      const { refreshToken } = useAuthStore.getState();

      const result = await refreshToken();

      expect(result).toBe(false);
    });

    it('should logout when refresh fails', async () => {
      useAuthStore.setState({
        user: mockUser,
        tokens: mockTokens,
        isAuthenticated: true,
      });

      server.use(
        http.post('/api/v1/auth/refresh', () => {
          return HttpResponse.json({ detail: 'Token expired' }, { status: 401 });
        })
      );

      const { refreshToken } = useAuthStore.getState();

      const result = await refreshToken();

      expect(result).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({ error: 'Some error' });

      const { clearError } = useAuthStore.getState();
      clearError();

      expect(useAuthStore.getState().error).toBeNull();
    });
  });

  describe('setTokens', () => {
    it('should set tokens and mark as authenticated', () => {
      const { setTokens } = useAuthStore.getState();

      setTokens(mockTokens);

      const state = useAuthStore.getState();
      expect(state.tokens).toEqual(mockTokens);
      expect(state.isAuthenticated).toBe(true);
    });
  });
});
