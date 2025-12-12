import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Server,
  Activity,
  Box,
  Users,
  FileText,
  ScrollText,
  Settings,
  Menu,
  X,
  Bell,
  Search,
  ChevronDown,
} from 'lucide-react';
import { clsx } from 'clsx';

import { WebSocketIndicator } from '@/components/ui/WebSocketIndicator';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Agents', href: '/agents', icon: Server },
  { name: 'Services', href: '/services', icon: Activity },
  { name: 'Containers', href: '/containers', icon: Box },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Audit Logs', href: '/audit', icon: FileText },
  { name: 'Logs', href: '/logs', icon: ScrollText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-gray-900 border-r border-gray-800 transition-transform duration-300 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emma-400 to-emma-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">eM</span>
            </div>
            <span className="text-xl font-bold text-gradient">eMMA</span>
          </div>
          <button
            className="lg:hidden text-gray-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname.startsWith(item.href);
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200',
                  isActive
                    ? 'text-white bg-emma-600/20 border-l-2 border-emma-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                )}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* System Status */}
        <div className="p-4 border-t border-gray-800">
          <div className="p-3 rounded-lg bg-gray-800/50">
            <div className="flex items-center gap-2 text-sm">
              <span className="status-healthy" />
              <span className="text-gray-300">System Healthy</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">Last check: 2 min ago</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-4 lg:px-6 border-b border-gray-800 bg-gray-900/95 backdrop-blur-sm sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden text-gray-400 hover:text-white"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={24} />
            </button>

            {/* Search */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 w-64">
              <Search size={18} className="text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="bg-transparent border-none outline-none text-sm text-gray-200 placeholder-gray-500 w-full"
              />
              <kbd className="hidden md:inline-flex text-xs text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">
                ⌘K
              </kbd>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* WebSocket Status */}
            <WebSocketIndicator />

            {/* Notifications */}
            <button className="relative p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
              <Bell size={20} />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {/* User menu */}
            <button className="flex items-center gap-2 p-2 hover:bg-gray-800 rounded-lg transition-colors">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emma-400 to-emma-600 flex items-center justify-center">
                <span className="text-white text-sm font-medium">D</span>
              </div>
              <span className="hidden md:block text-sm font-medium text-gray-200">
                Dominique
              </span>
              <ChevronDown size={16} className="text-gray-400" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
