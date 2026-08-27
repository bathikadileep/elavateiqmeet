import React, { useEffect, useState, useCallback } from 'react';
import notificationsApi from '../../api/notifications';
import type { NotificationItem } from '../../types/notifications';
import Badge from '../common/Badge';
import { Bell, CheckCheck, X, Clock, Video, UserPlus, FileText, AlertTriangle } from 'lucide-react';

export interface NotificationDrawerProps {
  onClose: () => void;
  onCountUpdated?: (newCount: number) => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({ onClose, onCountUpdated }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchNotifs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notificationsApi.list();
      setNotifications(res.notifications);
      setUnreadCount(res.unread_count);
      if (onCountUpdated) onCountUpdated(res.unread_count);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [onCountUpdated]);

  useEffect(() => {
    fetchNotifs();
  }, [fetchNotifs]);

  const handleMarkRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      const nextCount = Math.max(0, unreadCount - 1);
      setUnreadCount(nextCount);
      if (onCountUpdated) onCountUpdated(nextCount);
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
      if (onCountUpdated) onCountUpdated(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const getNotifIcon = (type: string) => {
    switch (type) {
      case 'meeting_start':
      case 'meeting_invite':
        return <Video className="w-4 h-4 text-indigo-400" />;
      case 'participant_join':
      case 'participant_leave':
        return <UserPlus className="w-4 h-4 text-cyan-400" />;
      case 'file_shared':
        return <FileText className="w-4 h-4 text-purple-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl glass-card border border-white/10 p-4 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-150 bg-[#080911]/95 backdrop-blur-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-white">Notifications Inbox</h3>
          {unreadCount > 0 && <Badge variant="info" size="sm">{unreadCount} New</Badge>}
        </div>

        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              title="Mark all as read"
              className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Read All</span>
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notifications Feed */}
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {loading ? (
          <div className="py-8 text-center text-xs text-gray-400">Loading inbox...</div>
        ) : notifications.length === 0 ? (
          <div className="py-8 text-center text-xs text-gray-400 space-y-1">
            <Bell className="w-8 h-8 text-gray-600 mx-auto stroke-1" />
            <p>No notifications in your inbox.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
              className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                n.is_read
                  ? 'bg-white/[0.01] border-white/5 opacity-70'
                  : 'bg-indigo-500/10 border-indigo-500/20 hover:border-indigo-500/40'
              }`}
            >
              <div className="p-2 rounded-lg bg-white/5 shrink-0 mt-0.5">
                {getNotifIcon(n.type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-bold text-white truncate">{n.title}</h4>
                  {!n.is_read && <span className="w-2 h-2 rounded-full bg-indigo-500 shrink-0" />}
                </div>

                {n.body && <p className="text-[11px] text-gray-300 mt-0.5 line-clamp-2">{n.body}</p>}

                <span className="text-[10px] text-gray-400 font-mono mt-1 block flex items-center gap-1">
                  <Clock className="w-3 h-3 text-gray-500" />
                  {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationDrawer;
