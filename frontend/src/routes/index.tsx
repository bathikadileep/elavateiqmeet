import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import PublicOnlyRoute from './PublicOnlyRoute';
import RequireRole from './RequireRole';
import MainLayout from '../components/layout/MainLayout';
import AuthLayout from '../components/layout/AuthLayout';
import MeetingLayout from '../components/layout/MeetingLayout';

// Auth Pages
import Login from '../pages/Login';
import Register from '../pages/Register';
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';
import ChangePassword from '../pages/ChangePassword';

// Meeting & App Pages
import Dashboard from '../pages/Dashboard';
import MeetingSchedule from '../pages/MeetingSchedule';
import MeetingHistory from '../pages/MeetingHistory';
import MeetingRoom from '../pages/MeetingRoom';
import FileManager from '../pages/FileManager';
import AdminPanel from '../pages/AdminPanel';
import ReportsHub from '../pages/ReportsHub';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* ── Public Auth Routes ────────────────────────────────────────────── */}
      <Route
        element={
          <PublicOnlyRoute>
            <AuthLayout />
          </PublicOnlyRoute>
        }
      >
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
      </Route>

      {/* ── Protected App Shell Routes ──────────────────────────────────────── */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/admin"
          element={
            <RequireRole allowedRoles={['super_admin']}>
              <AdminPanel />
            </RequireRole>
          }
        />
        <Route path="/meeting/new" element={<MeetingSchedule />} />
        <Route path="/history" element={<MeetingHistory />} />
        <Route path="/reports" element={<ReportsHub />} />
        <Route path="/reports/attendance" element={<ReportsHub />} />
        <Route path="/files" element={<FileManager />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route path="/settings" element={<ChangePassword />} />
        <Route path="/profile" element={<div className="p-4 glass-card rounded-2xl text-white">User Profile Settings</div>} />
      </Route>

      {/* ── Immersive Meeting Room Viewport ─────────────────────────────────── */}
      <Route
        element={
          <ProtectedRoute>
            <MeetingLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/room/:code" element={<MeetingRoom />} />
      </Route>

      {/* ── Root & Fallback Redirection ────────────────────────────────────── */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default AppRoutes;
