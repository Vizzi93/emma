// User Types

export type UserRole = 'admin' | 'operator' | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserSession {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  by_role: Record<UserRole, number>;
  active_sessions: number;
}

export interface CreateUserRequest {
  email: string;
  password: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface UpdateUserRequest {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}
