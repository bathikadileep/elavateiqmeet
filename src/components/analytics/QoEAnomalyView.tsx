import React from 'react';
import { Activity, AlertTriangle, Wifi, SignalHigh, TrendingUp } from 'lucide-react';

export const QoEAnomalyView: React.FC<{ meetingCode?: string }> = ({ meetingCode = 'room-101' }) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-cyan-400" />
          <div>
            <h2 className="text-lg font-bold text-white">QoE Network Anomaly Monitor</h2>
            <p className="text-xs text-slate-400">Real-time WebRTC frame telemetry & jitter alerts for room {meetingCode}</p>
          </div>
        </div>
        <span className="flex items-center gap-2 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300">
          <SignalHigh className="h-3.5 w-3.5" /> MOS: 4.45 (Excellent)
        </span>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Avg Bitrate</span>
          <div className="mt-1 text-xl font-bold text-cyan-400">2.4 Mbps</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Packet Loss</span>
          <div className="mt-1 text-xl font-bold text-emerald-400">0.02%</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Jitter</span>
          <div className="mt-1 text-xl font-bold text-amber-400">8.5 ms</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Round Trip Time</span>
          <div className="mt-1 text-xl font-bold text-indigo-400">28 ms</div>
        </div>
      </div>
    </div>
  );
};
