import React from 'react';
import GlassCard from '../common/GlassCard';
import { PieChart, ShieldCheck, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { DashboardStats } from '../../types/dashboard';

export interface AttendanceSummaryWidgetProps {
  stats: DashboardStats;
}

export const AttendanceSummaryWidget: React.FC<AttendanceSummaryWidgetProps> = ({ stats }) => {
  return (
    <GlassCard variant="default" className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-white/10 pb-3">
        <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
          <PieChart className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Attendance Summary</h3>
          <p className="text-xs text-gray-400">Session metrics & integrity score</p>
        </div>
      </div>

      {/* Progress Ring & Breakdown */}
      <div className="flex-1 flex flex-col justify-center space-y-4 py-2">
        <div className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/5">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-gray-400 uppercase">Reliability Rating</span>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black text-white">{stats.attendance_rate}%</span>
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <p className="text-[11px] text-gray-400">Based on prompt joins & completed sessions</p>
          </div>

          {/* Visual Circle Representation */}
          <div className="relative w-14 h-14 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-white/10"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-indigo-400"
                strokeDasharray={`${stats.attendance_rate}, 100`}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
          </div>
        </div>

        {/* Breakdown Items */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-white/5">
            <div className="flex items-center gap-2 text-gray-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>On-Time Attendance</span>
            </div>
            <span className="font-semibold text-white">100%</span>
          </div>

          <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-white/5">
            <div className="flex items-center gap-2 text-gray-300">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Missed Invitations</span>
            </div>
            <span className="font-semibold text-white">0</span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default AttendanceSummaryWidget;
