import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  Users as UsersIcon, UserPlus, Search, Shield, User as UserIcon, Eye,
  RefreshCw, MoreVertical, Key, Trash2, Ban, CheckCircle, XCircle,
  Crown, Wrench,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { useUsers, useUserStats, useCreateUser, useUpdateUser, useDeleteUser, useResetPassword } from '@/hooks/useUsers';
import type { User, UserRole } from '@/types/user';

const ROLE_CONFIG: Record<UserRole, { icon: typeof Crown; color: string; label: string }> = {
  admin: { icon: Crown, color: 'text-yellow-400', label: 'Admin' },
  operator: { icon: Wrench, color: 'text-blue-400', label: 'Operator' },
  viewer: { icon: Eye, color: 'text-gray-400', label: 'Viewer' },
};

function CreateUserModal({ onClose }: { onClose: () => void }) {
  const createUser = useCreateUser();
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'viewer' as UserRole });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createUser.mutateAsync(form);
      toast.success('Benutzer erstellt');
      onClose();
    } catch { toast.error('Fehler beim Erstellen'); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="card p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-4">Neuer Benutzer</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">E-Mail</label>
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Passwort</label>
            <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input" placeholder="Min. 8 Zeichen" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name (optional)</label>
            <input type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="input" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Rolle</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })} className="input">
              <option value="viewer">Viewer</option>
              <option value="operator">Operator</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">Abbrechen</button>
            <button type="submit" disabled={createUser.isPending} className="btn-primary flex-1">
              {createUser.isPending ? 'Erstelle...' : 'Erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UserRow({ user, onEdit }: { user: User; onEdit: (user: User) => void }) {
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();
  const resetPassword = useResetPassword();
  const [showMenu, setShowMenu] = useState(false);

  const roleConfig = ROLE_CONFIG[user.role];
  const RoleIcon = roleConfig.icon;

  const handleToggleActive = async () => {
    try {
      await updateUser.mutateAsync({ id: user.id, data: { is_active: !user.is_active } });
      toast.success(user.is_active ? 'Benutzer deaktiviert' : 'Benutzer aktiviert');
    } catch { toast.error('Fehler'); }
  };

  const handleResetPassword = async () => {
    const newPassword = prompt('Neues Passwort eingeben (min. 8 Zeichen):');
    if (!newPassword || newPassword.length < 8) return;
    try {
      await resetPassword.mutateAsync({ id: user.id, newPassword });
      toast.success('Passwort zurückgesetzt');
    } catch { toast.error('Fehler'); }
  };

  const handleDelete = async () => {
    if (!confirm(`Benutzer "${user.email}" wirklich löschen?`)) return;
    try {
      await deleteUser.mutateAsync(user.id);
      toast.success('Benutzer gelöscht');
    } catch { toast.error('Fehler beim Löschen'); }
  };

  return (
    <div className={`card p-4 border ${user.is_active ? 'border-gray-800' : 'border-red-900/50 bg-red-900/10'} transition-all hover:border-gray-600`}>
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg bg-gray-800 ${user.is_active ? roleConfig.color : 'text-gray-600'}`}>
          <RoleIcon size={24} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-white">{user.full_name || user.email}</span>
            <span className={`px-2 py-0.5 text-xs rounded ${roleConfig.color} bg-gray-800`}>{roleConfig.label}</span>
            {!user.is_active && <span className="px-2 py-0.5 text-xs rounded bg-red-900/50 text-red-400">Deaktiviert</span>}
          </div>
          <p className="text-sm text-gray-400">{user.email}</p>
        </div>

        <div className="hidden md:block text-right text-sm">
          <p className="text-gray-400">{user.last_login_at ? formatDistanceToNow(new Date(user.last_login_at), { addSuffix: true, locale: de }) : 'Nie'}</p>
          <p className="text-gray-500 text-xs">Letzter Login</p>
        </div>

        <div className="relative">
          <button onClick={() => setShowMenu(!showMenu)} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
            <MoreVertical size={18} />
          </button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-full mt-1 z-20 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1">
                <button onClick={handleToggleActive} className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center gap-2">
                  {user.is_active ? <><Ban size={16} /> Deaktivieren</> : <><CheckCircle size={16} /> Aktivieren</>}
                </button>
                <button onClick={handleResetPassword} className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center gap-2">
                  <Key size={16} /> Passwort zurücksetzen
                </button>
                <button onClick={handleDelete} className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-gray-700 flex items-center gap-2">
                  <Trash2 size={16} /> Löschen
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function Users() {
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [showInactive, setShowInactive] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: usersData, isLoading, refetch } = useUsers({
    include_inactive: showInactive,
    role: roleFilter !== 'all' ? roleFilter : undefined,
    search: searchQuery || undefined,
  });
  const { data: stats } = useUserStats();

  const users = usersData?.items || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Benutzerverwaltung</h1>
          <p className="text-gray-400 mt-1">Benutzer, Rollen und Sessions verwalten</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <UserPlus size={18} /> Benutzer hinzufügen
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emma-900/30 text-emma-400"><UsersIcon size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.total_users}</p><p className="text-sm text-gray-400">Gesamt</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-900/30 text-green-400"><CheckCircle size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.active_users}</p><p className="text-sm text-gray-400">Aktiv</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-900/30 text-yellow-400"><Crown size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.by_role?.admin || 0}</p><p className="text-sm text-gray-400">Admins</p></div>
          </div></div>
          <div className="card p-4"><div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-900/30 text-purple-400"><Shield size={20} /></div>
            <div><p className="text-2xl font-bold text-white">{stats.active_sessions}</p><p className="text-sm text-gray-400">Sessions</p></div>
          </div></div>
        </div>
      )}

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" placeholder="Suche nach E-Mail oder Name..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="input pl-10" />
          </div>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="input w-36">
            <option value="all">Alle Rollen</option>
            <option value="admin">Admin</option>
            <option value="operator">Operator</option>
            <option value="viewer">Viewer</option>
          </select>
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} className="rounded bg-gray-800 border-gray-600" />
            Inaktive
          </label>
          <button onClick={() => refetch()} className="btn-ghost"><RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} /></button>
        </div>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="card p-8 text-center text-gray-400"><RefreshCw size={24} className="mx-auto animate-spin mb-2" />Lade Benutzer...</div>
        ) : users.length > 0 ? (
          users.map((user) => <UserRow key={user.id} user={user} onEdit={() => {}} />)
        ) : (
          <div className="card p-8 text-center">
            <UsersIcon size={48} className="mx-auto text-gray-600 mb-4" />
            <p className="text-gray-400">Keine Benutzer gefunden</p>
          </div>
        )}
      </div>

      {showCreateModal && <CreateUserModal onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}
