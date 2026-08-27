import React, { useEffect, useState } from 'react';
import { useSocket } from '../../contexts/SocketContext';
import { Bell, X } from 'lucide-react';
import type { NotificationItem } from '../../types/notifications';

export const NotificationToast: React.FC = () => {
  const { socket } = useSocket();
  const [activeToast, setActiveToast] = useState<NotificationItem | null>(null);

  useEffect(() => {
    if (!socket) return;

    const handleNewNotification = (notif: NotificationItem) => {
      setActiveToast(notif);
      // Auto-hide toast after 5 seconds
      setTimeout(() => {
        setActiveToast(null);
      }, 5000);
    };

    socket.on('new_notification', handleNewNotification);

    return () => {
      socket.off('new_notification', handleNewNotification);
    };
  }, [socket]);

  if (!activeToast) return null;

  return (
    <div className="fixed top-20 right-6 z-50 max-w-sm w-full p-4 rounded-2xl glass-card border border-indigo-500/30 bg-[#080911]/90 backdrop-blur-2xl shadow-2xl animate-in slide-in-from-top-4 duration-200">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shrink-0">
          <Bell className="w-5 h-5 animate-pulse" />
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-bold text-white">{activeToast.title}</h4>
          {activeToast.body && <p className="text-[11px] text-gray-300 mt-0.5">{activeToast.body}</p>}
        </div>

        <button
          onClick={() => setActiveToast(null)}
          className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default NotificationToast;
