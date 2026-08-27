import React, { useEffect, useState, useCallback } from 'react';
import meetingsApi from '../api/meetings';
import attendanceApi from '../api/attendance';
import type { Meeting } from '../types/meeting';
import type { AttendanceSummary, ParticipantRosterItem } from '../types/attendance';
import GlassCard from '../components/common/GlassCard';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import { PieChart, Download, Calendar, Users, Clock, ShieldCheck, FileSpreadsheet } from 'lucide-react';

export const AttendanceReport: React.FC = () => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeetingId, setSelectedMeetingId] = useState<string>('');
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [roster, setRoster] = useState<ParticipantRosterItem[]>([]);
  const [activeMeetingTitle, setActiveMeetingTitle] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, meetingsRes] = await Promise.all([
        attendanceApi.getSummary(),
        meetingsApi.list(),
      ]);
      setSummary(sumRes);
      setMeetings(meetingsRes.meetings);

      if (meetingsRes.meetings.length > 0) {
        const first = meetingsRes.meetings[0];
        setSelectedMeetingId(first.id);
        setActiveMeetingTitle(first.title);
        fetchReport(first.id);
      }
    } catch (err) {
      console.error('Failed to load attendance metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchReport = async (meetingId: string) => {
    if (!meetingId) return;
    setReportLoading(true);
    try {
      const res = await attendanceApi.getMeetingReport(meetingId);
      setRoster(res.roster);
    } catch (err) {
      console.error('Failed to load meeting attendance report:', err);
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectMeeting = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedMeetingId(id);
    const m = meetings.find((item) => item.id === id);
    if (m) setActiveMeetingTitle(m.title);
    fetchReport(id);
  };

  const handleExportCSV = () => {
    if (roster.length === 0) return;
    const headers = ['Name', 'Email', 'Role', 'Status', 'Join Time', 'Leave Time', 'Duration (Mins)', 'Attendance %'];
    const rows = roster.map((r) => [
      `"${r.name}"`,
      `"${r.email}"`,
      `"${r.role}"`,
      `"${r.status}"`,
      `"${r.join_time}"`,
      `"${r.leave_time || 'N/A'}"`,
      r.duration_minutes,
      `${r.attendance_percentage}%`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Attendance_Report_${selectedMeetingId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return <Spinner fullScreen text="Loading attendance analytics..." />;
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Attendance Tracking & Compliance Reports</h1>
          <p className="text-xs text-gray-400">Detailed participant join/leave audit trail & duration analytics</p>
        </div>

        <Button
          variant="secondary"
          disabled={roster.length === 0}
          onClick={handleExportCSV}
          leftIcon={<Download className="w-4 h-4" />}
        >
          Export CSV Report
        </Button>
      </div>

      {/* Summary Cards Row */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard variant="default" className="p-4 flex items-center justify-between border-indigo-500/20">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Sessions</p>
              <h3 className="text-2xl font-extrabold text-white mt-1">{summary.total_joined + summary.total_hosted}</h3>
            </div>
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Calendar className="w-5 h-5" />
            </div>
          </GlassCard>

          <GlassCard variant="default" className="p-4 flex items-center justify-between border-cyan-500/20">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Time Spent</p>
              <h3 className="text-2xl font-extrabold text-white mt-1">{summary.total_hours} hrs</h3>
            </div>
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Clock className="w-5 h-5" />
            </div>
          </GlassCard>

          <GlassCard variant="default" className="p-4 flex items-center justify-between border-amber-500/20">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Avg Session Duration</p>
              <h3 className="text-2xl font-extrabold text-white mt-1">{summary.avg_duration_minutes} mins</h3>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
              <PieChart className="w-5 h-5" />
            </div>
          </GlassCard>

          <GlassCard variant="default" className="p-4 flex items-center justify-between border-emerald-500/20">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Attendance Score</p>
              <h3 className="text-2xl font-extrabold text-white mt-1">{summary.attendance_percentage}%</h3>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </GlassCard>
        </div>
      )}

      {/* Meeting Selection Header Bar */}
      <GlassCard variant="subtle" className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
          <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
            Select Meeting Report:
          </label>
        </div>

        <select
          value={selectedMeetingId}
          onChange={handleSelectMeeting}
          className="w-full sm:w-80 glass-input text-xs py-2 px-3 rounded-xl focus:outline-none bg-[#080911]"
        >
          {meetings.map((m) => (
            <option key={m.id} value={m.id}>
              {m.title} ({m.meeting_code})
            </option>
          ))}
        </select>
      </GlassCard>

      {/* Participant Roster Table */}
      <GlassCard variant="default" className="p-6">
        <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            <span>Participant Roster & Time Audit ({activeMeetingTitle})</span>
          </h3>

          <Badge variant="info" size="sm">
            {roster.length} Participants
          </Badge>
        </div>

        {reportLoading ? (
          <Spinner text="Loading roster audit log..." />
        ) : roster.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-xs">
            No participants joined this meeting yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Participant</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Join Time</th>
                  <th className="py-3 px-4">Leave Time</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Attendance %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-gray-300">
                {roster.map((p) => (
                  <tr key={p.participant_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white">
                      <div>{p.name}</div>
                      <div className="text-[10px] text-gray-400">{p.email}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge variant={p.role === 'host' ? 'warning' : 'neutral'} size="sm">
                        {p.role}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px]">
                      {new Date(p.join_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px]">
                      {p.leave_time
                        ? new Date(p.leave_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                        : 'Active / Still in room'}
                    </td>
                    <td className="py-3.5 px-4 font-medium">{p.duration_minutes} mins</td>
                    <td className="py-3.5 px-4 w-40">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                            style={{ width: `${p.attendance_percentage}%` }}
                          />
                        </div>
                        <span className="font-bold text-white text-[11px] min-w-[36px]">
                          {p.attendance_percentage}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  );
};

export default AttendanceReport;
