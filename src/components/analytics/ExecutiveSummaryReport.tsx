import React from 'react';
import { FileText, Download, Share2, Sparkles, CheckCircle2 } from 'lucide-react';

export const ExecutiveSummaryReport: React.FC = () => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-cyan-400" />
          <div>
            <h2 className="text-lg font-bold text-white">AI Executive Summary & Insights</h2>
            <p className="text-xs text-slate-400">Automated key decisions, action items, and sentiment analysis</p>
          </div>
        </div>
        <button className="flex items-center gap-2 rounded-xl bg-cyan-500/20 px-4 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/30">
          <Download className="h-4 w-4" /> Export PDF
        </button>
      </div>

      <div className="mt-6 space-y-4 text-sm text-slate-300">
        <div className="rounded-xl bg-slate-950/60 p-4 border border-slate-800">
          <h3 className="font-semibold text-cyan-300">Executive Briefing</h3>
          <p className="mt-2 leading-relaxed text-xs text-slate-400">
            The team discussed the Q4 WebRTC scaling strategy, approving the migration to SFU simulcast layers and automated recording transcoding. All action items were assigned with a target completion for next sprint.
          </p>
        </div>

        <div className="rounded-xl bg-slate-950/60 p-4 border border-slate-800">
          <h3 className="font-semibold text-emerald-400">Key Decisions Made</h3>
          <ul className="mt-2 space-y-1.5 text-xs text-slate-300">
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Standardized WebRTC SFrame E2EE encryption protocol</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Approved Okta SCIM 2.0 user provisioning integration</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
