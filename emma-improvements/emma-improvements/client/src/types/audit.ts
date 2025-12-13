// Audit Log Types

export interface AuditLog {
  id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  user_id: string | null;
  user_email: string | null;
  ip_address: string | null;
  description: string | null;
  details: Record<string, unknown> | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  success: boolean;
  error_message: string | null;
  created_at: string;
}

export interface AuditStats {
  total_events: number;
  successful: number;
  failed: number;
  by_action: Record<string, number>;
  unique_users: number;
  period_days: number;
}

export type AuditActionCategory = 'auth' | 'user' | 'service' | 'container' | 'system';

export const ACTION_LABELS: Record<string, string> = {
  'auth.login': 'Login',
  'auth.login_failed': 'Login fehlgeschlagen',
  'auth.logout': 'Logout',
  'auth.register': 'Registrierung',
  'auth.password_change': 'Passwort geändert',
  'auth.password_reset': 'Passwort zurückgesetzt',
  'user.create': 'User erstellt',
  'user.update': 'User aktualisiert',
  'user.delete': 'User gelöscht',
  'user.deactivate': 'User deaktiviert',
  'user.activate': 'User aktiviert',
  'user.session_revoke': 'Session beendet',
  'service.create': 'Service erstellt',
  'service.update': 'Service aktualisiert',
  'service.delete': 'Service gelöscht',
  'service.toggle': 'Service umgeschaltet',
  'service.check': 'Health Check',
  'container.start': 'Container gestartet',
  'container.stop': 'Container gestoppt',
  'container.restart': 'Container neugestartet',
  'container.remove': 'Container entfernt',
  'system.startup': 'System gestartet',
  'system.shutdown': 'System gestoppt',
};
