import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import dashboardApi from '../api/dashboard';
import type { DashboardOverviewResponse } from '../types/dashboard';
import StatsOverviewWidget from '../components/dashboard/StatsOverviewWidget';
import TodaysMeetingsWidget from '../components/dashboard/TodaysMeetingsWidget';
import UpcomingMeetingsWidget from '../components/dashboard/UpcomingMeetingsWidget';
import AttendanceSummaryWidget from '../components/dashboard/AttendanceSummaryWidget';
import NotificationsWidget from '../components/dashboard/NotificationsWidget';
import RecentActivityWidget from '../components/dashboard/RecentActivityWidget';
import Spinner from '../components/common/Spinner';
import Button from '../components/common/Button';
import { RefreshCw, Video, Plus, LogIn, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const INITIAL_DASHBOARD_DATA: DashboardOverviewResponse = {
  stats: {
    hosted_count: 0,
    joined_count: 0,
    total_minutes: 0,
    total_hours: 0,
    unread_notifications: 0,
    attendance_rate: 100,
  },
  todays_meetings: [],
  upcoming_meetings: [],
  notifications: [],
  recent_activity: [],
};

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState<DashboardOverviewResponse>(INITIAL_DASHBOARD_DATA);
  const [refreshing, setRefreshing] = useState(false);
  const [joinCode, setJoinCode] = useState('');

  const handleStartInstant = () => {
    const code = Math.random().toString(36).substring(2, 5) + '-' +
                 Math.random().toString(36).substring(2, 6) + '-' +
                 Math.random().toString(36).substring(2, 5);
    navigate(`/room/${code}`);
  };

  const handleJoinWithCode = (e: React.FormEvent) => {
    e.preventDefault();
    let code = joinCode.trim();
    if (!code) return;
    if (code.includes('/room/')) {
      code = code.split('/room/')[1].split('?')[0].split('#')[0];
    }
    navigate(`/room/${code}`);
  };

  const fetchOverview = useCallback(async () => {
    try {
      const res = await dashboardApi.getOverview();
      setData(res);
    } catch (err) {
      console.warn('Dashboard fetch failed, fallback to default state:', err);
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchOverview();
  };

  const handleMarkRead = async (id: string) => {
    try {
      await dashboardApi.markNotificationRead(id);
      setData((prev) => ({
        ...prev,
        notifications: prev.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true } : n
        ),
        stats: {
          ...prev.stats,
          unread_notifications: Math.max(0, prev.stats.unread_notifications - 1),
        },
      }));
    } catch (err) {
      console.error('Failed to mark notification read:', err);
    }
  };

  return (
    <div className="space-y-6 pb-8 animate-in fade-in duration-300">
      {/* Top Banner / Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-card p-6 rounded-2xl border-indigo-500/20 bg-gradient-to-r from-indigo-900/30 via-purple-900/20 to-cyan-900/20">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Welcome back, {user?.display_name || user?.username}! 👋
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            ElevateIQ Meeting Platform • Enterprise Workspace Dashboard
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            isLoading={refreshing}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleStartInstant}
            leftIcon={<Plus className="w-4 h-4" />}
            rightIcon={<Video className="w-4 h-4" />}
          >
            Start Meeting
          </Button>
        </div>
      </div>

      {/* Quick Action Hub: Start Meeting & Join with Code */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Start Instant Meeting */}
        <div className="glass-card p-5 rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/40 via-purple-950/20 to-[#0d0f1d] flex flex-col justify-between space-y-4">
          <div className="flex items-start gap-3.5">
            <div className="p-3 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Start a New Meeting</h3>
              <p className="text-xs text-gray-400 mt-0.5">Generate a secure room code and invite participants</p>
            </div>
          </div>
          <Button
            variant="primary"
            size="md"
            className="w-full"
            onClick={handleStartInstant}
            leftIcon={<Plus className="w-4 h-4" />}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Start Instant Meeting
          </Button>
        </div>

        {/* Card 2: Join Meeting with Code */}
        <div className="glass-card p-5 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-950/40 via-blue-950/20 to-[#0d0f1d] flex flex-col justify-between space-y-4">
          <div className="flex items-start gap-3.5">
            <div className="p-3 rounded-xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-400">
              <LogIn className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Join with Code or Link</h3>
              <p className="text-xs text-gray-400 mt-0.5">Paste meeting code or link shared by host</p>
            </div>
          </div>
          <form onSubmit={handleJoinWithCode} className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. dfa-2061-2b7 or paste link..."
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              className="flex-1 glass-input text-sm py-2 px-3.5 rounded-xl font-mono focus:outline-none"
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!joinCode.trim()}
              className="bg-cyan-600 hover:bg-cyan-500 text-white"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Join
            </Button>
          </form>
        </div>
      </div>

      {/* Row 1: Linear-Inspired Metrics Overview */}
      <StatsOverviewWidget stats={data.stats} />

      {/* Row 2: Main Grid Layout (Teams & Slack Inspired Widgets) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Today's & Upcoming Meetings */}
        <div className="lg:col-span-2 space-y-6">
          <TodaysMeetingsWidget meetings={data.todays_meetings} onMeetingCreated={fetchOverview} />
          <UpcomingMeetingsWidget meetings={data.upcoming_meetings} />
        </div>

        {/* Right 1 Column: Attendance Summary, Notifications & Activity */}
        <div className="space-y-6">
          <AttendanceSummaryWidget stats={data.stats} />
          <NotificationsWidget notifications={data.notifications} onMarkRead={handleMarkRead} />
          <RecentActivityWidget activities={data.recent_activity} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
