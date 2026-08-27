import React from 'react';
import GlassCard from '../common/GlassCard';
import { Activity, LogIn, LogOut, ShieldAlert, Mic, MicOff } from 'lucide-react';
import type { ActivityItem } from '../../types/dashboard';

export interface RecentActivityWidgetProps {
  activities: ActivityItem[];
}

export const RecentActivityWidget: React.FC<RecentActivityWidgetProps> = ({ activities }) => {
  const getEventIcon = (event: string) => {
    switch (event) {
      case 'joined':
        return <LogIn className="w-3.5 h-3.5 text-emerald-400" />;
      case 'left':
        return <LogOut className="w-3.5 h-3.5 text-gray-400" />;
      case 'kicked':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
      case 'muted':
        return <MicOff className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Mic className="w-3.5 h-3.5 text-indigo-400" />;
    }
  };

  return (
    <GlassCard variant="default" className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-white/10 pb-3">
        <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Recent Activity</h3>
          <p className="text-xs text-gray-400">Audit trail of room join/leave events</p>
        </div>
      </div>

      {/* Feed */}
      <div className="flex-1 space-y-2.5 overflow-y-auto max-h-[320px] pr-1">
        {activities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-400 space-y-2">
            <Activity className="w-10 h-10 text-gray-600 stroke-1" />
            <p className="text-xs">No recent activity logs recorded.</p>
          </div>
        ) : (
          activities.map((act) => (
            <div
              key={act.id}
              className="p-3 rounded-xl glass-card flex items-center justify-between gap-3 text-xs"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg bg-white/5">
                  {getEventIcon(act.event)}
                </div>
                <div>
                  <span className="font-semibold text-white capitalize">{act.event}</span> meeting room
                  {act.duration_seconds && (
                    <span className="text-gray-400 ml-1">({roundDuration(act.duration_seconds)})</span>
                  )}
                </div>
              </div>

              <span className="text-[11px] text-gray-400 font-mono">
                {new Date(act.event_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
};

function roundDuration(sec: number): string {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  return `${m}m`;
}

export default RecentActivityWidget;
