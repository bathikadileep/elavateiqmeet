import React from 'react';
import GlassCard from '../common/GlassCard';
import { Video, Users, Clock, Award } from 'lucide-react';
import type { DashboardStats } from '../../types/dashboard';

export interface StatsOverviewWidgetProps {
  stats: DashboardStats;
}

export const StatsOverviewWidget: React.FC<StatsOverviewWidgetProps> = ({ stats }) => {
  const statCards = [
    {
      title: 'Meetings Hosted',
      value: stats.hosted_count,
      unit: 'sessions',
      icon: Video,
      gradient: 'from-indigo-500/20 to-purple-500/20',
      borderColor: 'border-indigo-500/30',
      iconColor: 'text-indigo-400',
    },
    {
      title: 'Meetings Joined',
      value: stats.joined_count,
      unit: 'attended',
      icon: Users,
      gradient: 'from-cyan-500/20 to-blue-500/20',
      borderColor: 'border-cyan-500/30',
      iconColor: 'text-cyan-400',
    },
    {
      title: 'Total Meeting Time',
      value: `${stats.total_hours}h`,
      unit: `${stats.total_minutes} mins`,
      icon: Clock,
      gradient: 'from-amber-500/20 to-orange-500/20',
      borderColor: 'border-amber-500/30',
      iconColor: 'text-amber-400',
    },
    {
      title: 'Attendance Rate',
      value: `${stats.attendance_rate}%`,
      unit: 'reliability',
      icon: Award,
      gradient: 'from-emerald-500/20 to-teal-500/20',
      borderColor: 'border-emerald-500/30',
      iconColor: 'text-emerald-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((card, idx) => (
        <GlassCard
          key={idx}
          variant="hover"
          className={`relative overflow-hidden border ${card.borderColor} bg-gradient-to-br ${card.gradient}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {card.title}
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-extrabold text-white tracking-tight">
                  {card.value}
                </span>
                <span className="text-xs text-gray-400 font-medium">{card.unit}</span>
              </div>
            </div>

            <div className={`p-3 rounded-xl bg-white/5 border border-white/10 ${card.iconColor}`}>
              <card.icon className="w-6 h-6" />
            </div>
          </div>
        </GlassCard>
      ))}
    </div>
  );
};

export default StatsOverviewWidget;
