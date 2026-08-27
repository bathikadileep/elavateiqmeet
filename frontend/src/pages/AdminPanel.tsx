import React, { useEffect, useState, useCallback } from 'react';
import adminApi from '../api/admin';
import type {
  AdminMetrics,
  GrowthSeriesPoint,
  AdminUserItem,
  AdminMeetingItem,
  AdminRoleItem,
} from '../types/admin';
import GlassCard from '../components/common/GlassCard';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Avatar from '../components/common/Avatar';
import {
  ShieldCheck,
  Users,
  Video,
  BarChart3,
  Search,
  UserCheck,
  UserX,
  Trash2,
  PowerOff,
  Lock,
  HardDrive,
  TrendingUp,
} from 'lucide-react';

export const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'meetings' | 'roles'>('overview');

  // Overview State
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [growthSeries, setGrowthSeries] = useState<GrowthSeriesPoint[]>([]);

  // Users State
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [userSearch, setUserSearch] = useState('');

  // Meetings State
  const [meetings, setMeetings] = useState<AdminMeetingItem[]>([]);

  // Roles State
  const [roles, setRoles] = useState<AdminRoleItem[]>([]);

  const [loading, setLoading] = useState(true);

  const fetchOverview = useCallback(async () => {
    try {
      const res = await adminApi.getAnalytics();
      setMetrics(res.metrics);
      setGrowthSeries(res.growth_series);
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await adminApi.listUsers(userSearch);
      setUsers(res.users);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  }, [userSearch]);

  const fetchMeetings = useCallback(async () => {
    try {
      const res = await adminApi.listMeetings();
      setMeetings(res.meetings);
    } catch (err) {
      console.error('Failed to load meetings:', err);
    }
  }, []);

  const fetchRoles = useCallback(async () => {
    try {
      const res = await adminApi.listRoles();
      setRoles(res.roles);
    } catch (err) {
      console.error('Failed to load roles:', err);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchOverview(), fetchUsers(), fetchMeetings(), fetchRoles()]).finally(() => {
      setLoading(false);
    });
  }, [fetchOverview, fetchUsers, fetchMeetings, fetchRoles]);

  const handleToggleUserStatus = async (user: AdminUserItem) => {
    const nextStatus = user.status === 'active' ? 'suspended' : 'active';
    try {
      await adminApi.updateUserStatus(user.id, nextStatus);
      setUsers((prev) => prev.map((u) => (u.id === user.id ? { ...u, status: nextStatus } : u)));
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleDeleteUser = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await adminApi.deleteUser(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  const handleForceEndMeeting = async (id: string) => {
    try {
      await adminApi.forceEndMeeting(id);
      setMeetings((prev) => prev.map((m) => (m.id === id ? { ...m, status: 'ended' } : m)));
    } catch (err) {
      console.error('Failed to end meeting:', err);
    }
  };

  const handleDeleteMeeting = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this meeting?')) return;
    try {
      await adminApi.deleteMeeting(id);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error('Failed to delete meeting:', err);
    }
  };

  if (loading) {
    return <Spinner fullScreen text="Loading Enterprise Admin Control Center..." />;
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <ShieldCheck className="w-7 h-7 text-indigo-400" />
            <span>Enterprise Admin Control Center</span>
          </h1>
          <p className="text-xs text-gray-400">Platform-wide user RBAC, live meeting overrides, analytics, and security policy</p>
        </div>

        <Badge variant="warning" size="md">
          Super Admin Privileges
        </Badge>
      </div>

      {/* Navigation Tabs */}
      <GlassCard variant="subtle" className="p-2 flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'overview' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Analytics & Overview
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'users' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Users className="w-4 h-4" />
          User Management ({users.length})
        </button>

        <button
          onClick={() => setActiveTab('meetings')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'meetings' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Video className="w-4 h-4" />
          Meeting Management ({meetings.length})
        </button>

        <button
          onClick={() => setActiveTab('roles')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'roles' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Lock className="w-4 h-4" />
          Roles & Permissions ({roles.length})
        </button>
      </GlassCard>

      {/* ── TAB 1: OVERVIEW & ANALYTICS ────────────────────────────────────────── */}
      {activeTab === 'overview' && metrics && (
        <div className="space-y-6">
          {/* Metric Cards Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <GlassCard variant="default" className="p-4 border-indigo-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase">Platform Users</p>
                  <h3 className="text-2xl font-black text-white mt-1">{metrics.total_users}</h3>
                </div>
                <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
                  <Users className="w-5 h-5" />
                </div>
              </div>
              <p className="text-[11px] text-emerald-400 mt-2 font-medium">
                {metrics.active_users} active accounts
              </p>
            </GlassCard>

            <GlassCard variant="default" className="p-4 border-rose-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase">Live Meetings Now</p>
                  <h3 className="text-2xl font-black text-white mt-1">{metrics.live_meetings}</h3>
                </div>
                <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400">
                  <Video className="w-5 h-5" />
                </div>
              </div>
              <p className="text-[11px] text-gray-400 mt-2 font-medium">
                {metrics.total_meetings} total meetings held
              </p>
            </GlassCard>

            <GlassCard variant="default" className="p-4 border-purple-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase">Storage Consumed</p>
                  <h3 className="text-2xl font-black text-white mt-1">{metrics.total_storage_mb} MB</h3>
                </div>
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
                  <HardDrive className="w-5 h-5" />
                </div>
              </div>
              <p className="text-[11px] text-gray-400 mt-2 font-medium">
                {metrics.total_files} active files stored
              </p>
            </GlassCard>

            <GlassCard variant="default" className="p-4 border-emerald-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase">Platform Stream Time</p>
                  <h3 className="text-2xl font-black text-white mt-1">{metrics.total_platform_hours} hrs</h3>
                </div>
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>
              <p className="text-[11px] text-emerald-400 mt-2 font-medium">
                99.9% WebRTC Uptime
              </p>
            </GlassCard>
          </div>

          {/* SVG Growth Bar Chart */}
          <GlassCard variant="default" className="p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
              <span>Weekly Platform Growth & Meeting Volume</span>
            </h3>

            <div className="h-48 flex items-end justify-between gap-4 pt-8 px-4 border-b border-white/10 pb-2">
              {growthSeries.map((point) => {
                const heightPct = Math.min(100, Math.max(15, (point.meetings / (metrics.total_meetings || 1)) * 100));
                return (
                  <div key={point.label} className="flex-1 flex flex-col items-center gap-2 group">
                    <div className="w-full bg-white/5 rounded-t-xl overflow-hidden h-36 flex items-end">
                      <div
                        className="w-full bg-gradient-to-t from-indigo-600 via-purple-600 to-cyan-400 rounded-t-xl group-hover:brightness-125 transition-all"
                        style={{ height: `${heightPct}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-semibold text-gray-400">{point.label}</span>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        </div>
      )}

      {/* ── TAB 2: USER MANAGEMENT ────────────────────────────────────────────── */}
      {activeTab === 'users' && (
        <GlassCard variant="default" className="p-6 space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type="text"
                placeholder="Search user by name or email..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="w-full glass-input text-xs py-2 pl-9 pr-3 rounded-xl focus:outline-none"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Roles</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Joined Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-gray-300">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.display_name || u.username} size="sm" />
                        <div>
                          <div className="font-semibold text-white">{u.display_name || u.username}</div>
                          <div className="text-[10px] text-gray-400">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1">
                        {u.roles.map((r) => (
                          <Badge key={r} variant={r === 'super_admin' ? 'warning' : 'info'} size="sm">
                            {r}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge variant={u.status === 'active' ? 'success' : 'danger'} size="sm">
                        {u.status}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleUserStatus(u)}
                          leftIcon={u.status === 'active' ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                        >
                          {u.status === 'active' ? 'Suspend' : 'Activate'}
                        </Button>

                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          className="p-1.5 rounded-lg hover:bg-rose-500/20 text-gray-400 hover:text-rose-400 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {/* ── TAB 3: MEETING MANAGEMENT ─────────────────────────────────────────── */}
      {activeTab === 'meetings' && (
        <GlassCard variant="default" className="p-6 space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Meeting Title</th>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Host</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-gray-300">
                {meetings.map((m) => (
                  <tr key={m.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white">{m.title}</td>
                    <td className="py-3.5 px-4 font-mono text-indigo-300 font-bold">{m.meeting_code}</td>
                    <td className="py-3.5 px-4">{m.host_name}</td>
                    <td className="py-3.5 px-4">
                      <Badge variant={m.status === 'live' ? 'danger' : m.status === 'scheduled' ? 'info' : 'neutral'} size="sm">
                        {m.status}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {m.status === 'live' && (
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleForceEndMeeting(m.id)}
                            leftIcon={<PowerOff className="w-3.5 h-3.5" />}
                          >
                            Force End
                          </Button>
                        )}

                        <button
                          onClick={() => handleDeleteMeeting(m.id)}
                          className="p-1.5 rounded-lg hover:bg-rose-500/20 text-gray-400 hover:text-rose-400 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {/* ── TAB 4: ROLES & PERMISSIONS ───────────────────────────────────────── */}
      {activeTab === 'roles' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {roles.map((role) => (
            <GlassCard key={role.id} variant="glow" className="p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white capitalize">{role.name}</h3>
                <Badge variant={role.name === 'super_admin' ? 'warning' : 'info'} size="sm">
                  {role.is_system ? 'System Role' : 'Custom'}
                </Badge>
              </div>

              <p className="text-xs text-gray-400">{role.description || 'No description provided.'}</p>

              <div className="border-t border-white/10 pt-3">
                <span className="text-[11px] font-bold text-gray-300 uppercase tracking-wider block mb-2">
                  Granted Permissions:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {role.permissions.map((p) => (
                    <span key={p} className="px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] text-gray-300 font-mono">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
