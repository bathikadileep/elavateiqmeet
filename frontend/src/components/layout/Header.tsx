import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import notificationsApi from '../../api/notifications';
import Avatar from '../common/Avatar';
import NotificationDrawer from '../notifications/NotificationDrawer';
import BrandLogo from '../common/BrandLogo';
import { Video, LogOut, User as UserIcon, Bell, ChevronDown, ArrowRight } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [joinCodeInput, setJoinCodeInput] = useState('');

  useEffect(() => {
    if (user) {
      notificationsApi.list().then((res) => {
        setUnreadCount(res.unread_count);
      }).catch((err) => console.error('Failed to fetch initial unread count:', err));
    }
  }, [user]);

  const handleQuickJoin = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanCode = joinCodeInput.trim();
    if (cleanCode) {
      navigate(`/room/${cleanCode}`);
      setJoinCodeInput('');
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full h-16 bg-[#080911]/75 backdrop-blur-xl border-b border-white/[0.08] px-6 flex items-center justify-between">
      {/* Brand Identity */}
      <Link to="/dashboard" className="group">
        <BrandLogo size="md" showText={true} />
      </Link>

      {/* Quick Join Room by Code Bar */}
      <form onSubmit={handleQuickJoin} className="hidden md:flex items-center gap-2">
        <input
          type="text"
          placeholder="Enter Room Code (e.g. dfa-2061-2b7)..."
          value={joinCodeInput}
          onChange={(e) => setJoinCodeInput(e.target.value)}
          className="w-72 glass-input text-xs py-2 px-3.5 rounded-xl font-mono focus:outline-none"
        />
        <button
          type="submit"
          disabled={!joinCodeInput.trim()}
          className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
        >
          <span>Join</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </form>

      {/* Right Controls & User Profile */}
      <div className="flex items-center gap-4 relative">
        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            aria-label="Notifications"
            className="relative p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
              </span>
            )}
          </button>

          {/* Notification Inbox Drawer */}
          {notifOpen && (
            <NotificationDrawer
              onClose={() => setNotifOpen(false)}
              onCountUpdated={(newCount) => setUnreadCount(newCount)}
            />
          )}
        </div>

        {/* User Dropdown */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-white/5 transition-colors cursor-pointer border border-transparent hover:border-white/10"
            >
              <Avatar name={user.display_name || user.username} src={user.avatar_url} size="sm" status="online" />
              <span className="text-sm font-medium text-gray-200 max-w-[120px] truncate hidden sm:inline-block">
                {user.display_name || user.username}
              </span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
                <div className="absolute right-0 mt-2 w-56 rounded-2xl glass-card border border-white/10 p-2 shadow-2xl z-20 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-3 py-2 border-b border-white/5 mb-1">
                    <p className="text-xs font-semibold text-white truncate">{user.display_name}</p>
                    <p className="text-[11px] text-gray-400 truncate">@{user.username}</p>
                  </div>

                  <Link
                    to="/profile"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
                  >
                    <UserIcon className="w-4 h-4" />
                    Profile Settings
                  </Link>

                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors cursor-pointer mt-1"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
