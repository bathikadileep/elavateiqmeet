import React from 'react';
import { Outlet } from 'react-router-dom';
import { Video, ShieldCheck, Zap, Lock } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#080911] relative overflow-hidden p-4">
      {/* Background Animated Blobs */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-cyan-500/20 rounded-full blur-[120px] pointer-events-none animate-pulse" />

      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8 items-center z-10">
        {/* Left Hero Branding Section */}
        <div className="hidden md:flex flex-col space-y-6 p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Video className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-white">ElevateIQ</h1>
          </div>

          <h2 className="text-3xl font-extrabold leading-tight text-white">
            Next-Gen Enterprise <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Meeting Platform
            </span>
          </h2>

          <p className="text-sm text-gray-400 leading-relaxed">
            Experience ultra-low latency WebRTC peer-to-peer video streams, real-time collaboration, and enterprise-grade security encryption.
          </p>

          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-3 text-xs text-gray-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Role-Based Access Control (RBAC) Protection</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-300">
              <Zap className="w-4 h-4 text-cyan-400" />
              <span>Real-time Socket.IO Event Broadcasting</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-300">
              <Lock className="w-4 h-4 text-indigo-400" />
              <span>Secure HttpOnly JWT Token Sessions</span>
            </div>
          </div>
        </div>

        {/* Right Auth Form Outlet Container */}
        <div className="w-full">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
