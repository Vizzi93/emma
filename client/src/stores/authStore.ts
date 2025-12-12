import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import { api } from '@/lib/api';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  setTokens: (tokens: Tokens) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.post<{ user: User; tokens: Tokens }>('/auth/login', {
            email,
            password,
          });

          set({
            user: response.user,
            tokens: response.tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Login fehlgeschlagen';
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string, fullName?: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.post<{ user: User; tokens: Tokens }>('/auth/register', {
            email,
            password,
            full_name: fullName,
          });

          set({
            user: response.user,
            tokens: response.tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Registrierung fehlgeschlagen';
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        const { tokens } = get();

        try {
          if (tokens?.refresh_token) {
            await api.post('/auth/logout', {
              refresh_token: tokens.refresh_token,
            });
          }
        } catch {
          // Ignore logout errors
        } finally {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      refreshToken: async () => {
        const { tokens } = get();

        if (!tokens?.refresh_token) {
          return false;
        }

        try {
          const response = await api.post<{ access_token: string; expires_in: number }>(
            '/auth/refresh',
            { refresh_token: tokens.refresh_token }
          );

          set({
            tokens: {
              ...tokens,
              access_token: response.access_token,
              expires_in: response.expires_in,
            },
          });

          return true;
        } catch {
          // Refresh failed, logout user
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
          return false;
        }
      },

      fetchUser: async () => {
        try {
          const user = await api.get<User>('/auth/me');
          set({ user, isAuthenticated: true });
        } catch {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
        }
      },

      clearError: () => set({ error: null }),

      setTokens: (tokens: Tokens) => set({ tokens, isAuthenticated: true }),
    }),
    {
      name: 'emma-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        tokens: state.tokens,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper to get current access token
export const getAccessToken = () => useAuthStore.getState().tokens?.access_token;
