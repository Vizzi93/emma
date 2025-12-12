import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { DashboardLayout } from '@/components/layouts/DashboardLayout';
import { ProtectedRoute, GuestRoute } from '@/components/auth/ProtectedRoute';
import { Dashboard } from '@/pages/Dashboard';
import { Agents } from '@/pages/Agents';
import { AgentDetail } from '@/pages/AgentDetail';
import { Services } from '@/pages/Services';
import { Containers } from '@/pages/Containers';
import { Users } from '@/pages/Users';
import { AuditLogPage as AuditLogs } from '@/pages/AuditLog';
import { Logs } from '@/pages/Logs';
import { Settings } from '@/pages/Settings';
import { Login } from '@/pages/Login';
import { Register } from '@/pages/Register';
import { NotFound } from '@/pages/NotFound';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Auth Routes */}
        <Route
          path="/login"
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          }
        />

        {/* Protected Dashboard Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="agents" element={<Agents />} />
          <Route path="agents/:agentId" element={<AgentDetail />} />
          <Route path="services" element={<Services />} />
          <Route path="containers" element={<Containers />} />
          <Route path="users" element={<Users />} />
          <Route path="audit" element={<AuditLogs />} />
          <Route path="logs" element={<Logs />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
