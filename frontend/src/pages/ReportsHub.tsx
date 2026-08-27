import React, { useEffect, useState, useCallback } from 'react';
import reportsApi from '../api/reports';
import type {
  AttendanceReportRecord,
  MeetingReportRecord,
  UserActivityReportRecord,
} from '../types/reports';
import GlassCard from '../components/common/GlassCard';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import { FileText, Download, Printer, Users, Video, Clock, CheckCircle2 } from 'lucide-react';

export const ReportsHub: React.FC = () => {
  const [activeReport, setActiveReport] = useState<'attendance' | 'meetings' | 'user_activity'>('attendance');

  const [attendanceData, setAttendanceData] = useState<AttendanceReportRecord[]>([]);
  const [meetingData, setMeetingData] = useState<MeetingReportRecord[]>([]);
  const [userActivityData, setUserActivityData] = useState<UserActivityReportRecord[]>([]);

  const [loading, setLoading] = useState(true);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const [attRes, meetRes, userRes] = await Promise.all([
        reportsApi.getAttendanceReport(),
        reportsApi.getMeetingReport(),
        reportsApi.getUserActivityReport(),
      ]);
      setAttendanceData(attRes.data);
      setMeetingData(meetRes.data);
      setUserActivityData(userRes.data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handlePrintPDF = () => {
    window.print();
  };

  const handleExportFile = (format: 'csv' | 'excel') => {
    const reportKey = activeReport === 'user_activity' ? 'user-activity' : activeReport;
    const url = reportsApi.getExportUrl(reportKey, format);
    window.open(url, '_blank');
  };

  if (loading) {
    return <Spinner fullScreen text="Compiling executive reporting suite..." />;
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-indigo-400" />
            <span>Executive Reporting & Export Suite</span>
          </h1>
          <p className="text-xs text-gray-400">Generate, print PDF, and export CSV/Excel enterprise intelligence reports</p>
        </div>

        {/* Export Actions Bar */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrintPDF}
            leftIcon={<Printer className="w-4 h-4 text-indigo-400" />}
          >
            Print / Save PDF
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleExportFile('excel')}
            leftIcon={<Download className="w-4 h-4 text-emerald-400" />}
          >
            Excel (.xlsx)
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => handleExportFile('csv')}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <GlassCard variant="subtle" className="p-2 flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveReport('attendance')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeReport === 'attendance' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Clock className="w-4 h-4" />
          Attendance Report ({attendanceData.length})
        </button>

        <button
          onClick={() => setActiveReport('meetings')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeReport === 'meetings' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Video className="w-4 h-4" />
          Meeting History Report ({meetingData.length})
        </button>

        <button
          onClick={() => setActiveReport('user_activity')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeReport === 'user_activity' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
          }`}
        >
          <Users className="w-4 h-4" />
          User Activity Report ({userActivityData.length})
        </button>
      </GlassCard>

      {/* Printable Report Viewport */}
      <div id="printable-report">
        {/* ── 1. ATTENDANCE REPORT ──────────────────────────────────────────────── */}
        {activeReport === 'attendance' && (
          <GlassCard variant="default" className="p-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-indigo-400" />
                <span>Attendance Compliance Audit Log</span>
              </h3>
              <Badge variant="info" size="sm">
                {attendanceData.length} Records
              </Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4">Meeting Title</th>
                    <th className="py-3 px-4">Participant</th>
                    <th className="py-3 px-4">Event</th>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Compliance Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-gray-300">
                  {attendanceData.map((row) => (
                    <tr key={row.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">{row.meeting_title}</td>
                      <td className="py-3.5 px-4">{row.participant}</td>
                      <td className="py-3.5 px-4">
                        <Badge variant={row.event === 'joined' ? 'success' : 'neutral'} size="sm">
                          {row.event}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        {new Date(row.event_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 font-medium">{row.duration_minutes} mins</td>
                      <td className="py-3.5 px-4">
                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}

        {/* ── 2. MEETING HISTORY REPORT ───────────────────────────────────────── */}
        {activeReport === 'meetings' && (
          <GlassCard variant="default" className="p-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Video className="w-5 h-5 text-indigo-400" />
                <span>Platform Meeting History Audit</span>
              </h3>
              <Badge variant="info" size="sm">
                {meetingData.length} Meetings
              </Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4">Meeting Code</th>
                    <th className="py-3 px-4">Host Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Participants</th>
                    <th className="py-3 px-4">Created Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-gray-300">
                  {meetingData.map((m) => (
                    <tr key={m.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">{m.title}</td>
                      <td className="py-3.5 px-4 font-mono text-indigo-300 font-bold">{m.meeting_code}</td>
                      <td className="py-3.5 px-4">{m.host_name}</td>
                      <td className="py-3.5 px-4 capitalize">{m.meeting_type}</td>
                      <td className="py-3.5 px-4">
                        <Badge variant={m.status === 'live' ? 'danger' : 'neutral'} size="sm">
                          {m.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 font-bold">{m.participant_count}</td>
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        {new Date(m.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}

        {/* ── 3. USER ACTIVITY REPORT ─────────────────────────────────────────── */}
        {activeReport === 'user_activity' && (
          <GlassCard variant="default" className="p-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-indigo-400" />
                <span>User Activity & Engagement Analytics</span>
              </h3>
              <Badge variant="info" size="sm">
                {userActivityData.length} Users
              </Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Account Status</th>
                    <th className="py-3 px-4">Hosted Meetings</th>
                    <th className="py-3 px-4">Joined Sessions</th>
                    <th className="py-3 px-4">Active Hours</th>
                    <th className="py-3 px-4">Member Since</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-gray-300">
                  {userActivityData.map((u) => (
                    <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">
                        <div>{u.display_name}</div>
                        <div className="text-[10px] text-gray-400">@{u.username} • {u.email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge variant={u.status === 'active' ? 'success' : 'danger'} size="sm">
                          {u.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 font-bold">{u.hosted_count}</td>
                      <td className="py-3.5 px-4 font-bold">{u.joined_count}</td>
                      <td className="py-3.5 px-4 font-medium">{u.active_hours} hrs</td>
                      <td className="py-3.5 px-4 font-mono text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  );
};

export default ReportsHub;
