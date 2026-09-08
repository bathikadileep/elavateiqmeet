import React from 'react';
import { Users, HelpCircle, Hand, Video, TrendingUp } from 'lucide-react';

export const WebinarAnalyticsDashboard: React.FC = () => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Video className="h-6 w-6 text-pink-400" />
          <div>
            <h2 className="text-lg font-bold text-white">Webinar & Event Engagement Metrics</h2>
            <p className="text-xs text-slate-400">Live audience metrics, Q&A participation, and RTMP egress status</p>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Live Attendees</span>
          <div className="mt-1 text-2xl font-bold text-pink-400">1,248</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Q&A Questions</span>
          <div className="mt-1 text-2xl font-bold text-cyan-400">42</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">Hands Raised</span>
          <div className="mt-1 text-2xl font-bold text-amber-400">8</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <span className="text-xs text-slate-400">RTMP Egress</span>
          <div className="mt-1 text-2xl font-bold text-emerald-400">Streaming</div>
        </div>
      </div>
    </div>
  );
};
