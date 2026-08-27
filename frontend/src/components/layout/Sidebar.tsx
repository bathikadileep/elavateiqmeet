import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Video, History, Settings, ShieldCheck, FileSpreadsheet, Folder } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.roles?.includes('super_admin');

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'New Meeting', icon: Video, path: '/meeting/new' },
    { label: 'History', icon: History, path: '/history' },
    { label: 'Reports Suite', icon: FileSpreadsheet, path: '/reports' },
    { label: 'Files', icon: Folder, path: '/files' },
    { label: 'Settings', icon: Settings, path: '/settings' },
  ];

  if (isAdmin) {
    navItems.splice(1, 0, { label: 'Admin Panel', icon: ShieldCheck, path: '/admin' });
  }

  return (
    <aside className="w-64 h-[calc(100vh-4rem)] bg-[#080911]/50 backdrop-blur-xl border-r border-white/[0.08] p-4 flex flex-col justify-between hidden md:flex">
      <nav className="space-y-1.5">
        <div className="px-3 py-2 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
          Navigation
        </div>

        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-white border border-indigo-500/30 shadow-md shadow-indigo-500/10'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              }`
            }
          >
            <item.icon className="w-4 h-4 text-indigo-400" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* System Status Widget */}
      <div className="p-3.5 rounded-xl glass-card border border-white/5 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-gray-300">System Status</span>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>
        <p className="text-[11px] text-gray-400">WebRTC P2P Engine Operational</p>
      </div>
    </aside>
  );
};

export default Sidebar;
