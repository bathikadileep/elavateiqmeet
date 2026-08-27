import React from 'react';
import GlassCard from '../common/GlassCard';
import Badge from '../common/Badge';
import { Bell, Check, Info } from 'lucide-react';
import type { NotificationItem } from '../../types/dashboard';

export interface NotificationsWidgetProps {
  notifications: NotificationItem[];
  onMarkRead: (id: string) => void;
}

export const NotificationsWidget: React.FC<NotificationsWidgetProps> = ({
  notifications,
  onMarkRead,
}) => {
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <GlassCard variant="default" className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Notifications Inbox</h3>
            <p className="text-xs text-gray-400">System & room alerts</p>
          </div>
        </div>

        {unreadCount > 0 && (
          <Badge variant="info" size="sm">
            {unreadCount} Unread
          </Badge>
        )}
      </div>

      {/* Feed */}
      <div className="flex-1 space-y-2.5 overflow-y-auto max-h-[320px] pr-1">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-400 space-y-2">
            <Info className="w-10 h-10 text-gray-600 stroke-1" />
            <p className="text-xs">Your inbox is completely clear.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-3 rounded-xl transition-all flex items-start justify-between gap-3 ${
                n.is_read ? 'bg-white/[0.01] border border-white/5 opacity-70' : 'glass-card border-indigo-500/20'
              }`}
            >
              <div className="flex items-start gap-2.5">
                <div className={`p-1.5 rounded-lg mt-0.5 ${n.is_read ? 'bg-white/5 text-gray-500' : 'bg-indigo-500/20 text-indigo-400'}`}>
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-white">{n.title}</h4>
                  {n.body && <p className="text-[11px] text-gray-400 mt-0.5 leading-snug">{n.body}</p>}
                </div>
              </div>

              {!n.is_read && (
                <button
                  onClick={() => onMarkRead(n.id)}
                  title="Mark as read"
                  className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-emerald-400 transition-colors cursor-pointer shrink-0"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </GlassCard>
  );
};

export default NotificationsWidget;
