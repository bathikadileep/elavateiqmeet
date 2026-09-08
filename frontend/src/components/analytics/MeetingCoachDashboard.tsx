import React, { useState } from 'react';
import { Award, AlertTriangle, Users, Volume2, Clock, CheckCircle2, TrendingUp, Sparkles, MessageSquare } from 'lucide-react';

export interface ParticipantCoachStats {
  userId: string;
  displayName: string;
  talkTimeSec: number;
  talkTimePercentage: number;
  turnCount: number;
  averageWpm: number;
  monologueCount: number;
  interruptionsInitiated: number;
  interruptionsReceived: number;
  sentimentScore: number;
  energyLevel: number;
}

export interface MeetingCoachScorecard {
  roomCode: string;
  overallScore: number;
  inclusivityIndex: number;
  totalSpeechTimeSec: number;
  totalTurns: number;
  totalInterruptions: number;
  participants: ParticipantCoachStats[];
  recommendations: string[];
}

interface MeetingCoachDashboardProps {
  scorecard?: MeetingCoachScorecard;
  onClose?: () => void;
}

export const MeetingCoachDashboard: React.FC<MeetingCoachDashboardProps> = ({
  scorecard,
  onClose
}) => {
  // Mock fallback data for demonstration when live scorecard is warming up
  const data: MeetingCoachScorecard = scorecard || {
    roomCode: 'meet-quarterly-sync',
    overallScore: 88.5,
    inclusivityIndex: 82.4,
    totalSpeechTimeSec: 2450.0,
    totalTurns: 48,
    totalInterruptions: 3,
    participants: [
      {
        userId: 'u1',
        displayName: 'Sarah Connor (Host)',
        talkTimeSec: 1100,
        talkTimePercentage: 44.9,
        turnCount: 22,
        averageWpm: 135,
        monologueCount: 1,
        interruptionsInitiated: 1,
        interruptionsReceived: 1,
        sentimentScore: 0.65,
        energyLevel: 0.82
      },
      {
        userId: 'u2',
        displayName: 'David Miller',
        talkTimeSec: 850,
        talkTimePercentage: 34.7,
        turnCount: 18,
        averageWpm: 142,
        monologueCount: 0,
        interruptionsInitiated: 2,
        interruptionsReceived: 1,
        sentimentScore: 0.45,
        energyLevel: 0.74
      },
      {
        userId: 'u3',
        displayName: 'Elena Rostova',
        talkTimeSec: 500,
        talkTimePercentage: 20.4,
        turnCount: 8,
        averageWpm: 120,
        monologueCount: 0,
        interruptionsInitiated: 0,
        interruptionsReceived: 1,
        sentimentScore: 0.70,
        energyLevel: 0.65
      }
    ],
    recommendations: [
      'Strong engagement and respectful conversational turn-taking observed throughout.',
      'Sarah Connor had one 2.5-minute monologue during the roadmap review. Consider breaking longer updates into interactive prompts.',
      'Elena Rostova had lower airtime (20%). Passing direct questions can foster higher cross-functional contribution.'
    ]
  };

  const [activeTab, setActiveTab] = useState<'overview' | 'participants' | 'recommendations'>('overview');

  const formatSec = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}m ${s}s`;
  };

  return (
    <div className="w-full max-w-4xl bg-slate-900/95 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl text-white">
      {/* Header Bar */}
      <div className="px-8 py-6 border-b border-slate-800/80 flex items-center justify-between bg-gradient-to-r from-slate-900 via-slate-800/50 to-slate-900">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              AI Meeting Coach Intelligence
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Score: {data.overallScore} / 100
              </span>
            </h3>
            <p className="text-xs text-slate-400">Room Code: {data.roomCode} • Post-Meeting Scorecard</p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Close
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 px-8 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('overview')}
          className={`py-3 border-b-2 transition-all ${
            activeTab === 'overview' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Session Overview
        </button>
        <button
          onClick={() => setActiveTab('participants')}
          className={`py-3 border-b-2 transition-all ${
            activeTab === 'participants' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Participant Dynamics ({data.participants.length})
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`py-3 border-b-2 transition-all ${
            activeTab === 'recommendations' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Coach Recommendations ({data.recommendations.length})
        </button>
      </div>

      {/* Content Body */}
      <div className="p-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/40">
                <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <Award className="w-4 h-4 text-cyan-400" /> Inclusivity Index
                </span>
                <p className="text-2xl font-bold text-white">{data.inclusivityIndex}%</p>
                <span className="text-[11px] text-emerald-400 mt-1 block">Gini conversational balance</span>
              </div>

              <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/40">
                <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <Clock className="w-4 h-4 text-amber-400" /> Total Speech Time
                </span>
                <p className="text-2xl font-bold text-white">{formatSec(data.totalSpeechTimeSec)}</p>
                <span className="text-[11px] text-slate-400 mt-1 block">{data.totalTurns} speaker turns</span>
              </div>

              <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/40">
                <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <AlertTriangle className="w-4 h-4 text-rose-400" /> Interruptions
                </span>
                <p className="text-2xl font-bold text-white">{data.totalInterruptions}</p>
                <span className="text-[11px] text-slate-400 mt-1 block">Overlapping turns</span>
              </div>

              <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/40">
                <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <Users className="w-4 h-4 text-violet-400" /> Active Speakers
                </span>
                <p className="text-2xl font-bold text-white">{data.participants.length}</p>
                <span className="text-[11px] text-slate-400 mt-1 block">All participants voiced</span>
              </div>
            </div>

            {/* Talk Time Distribution Bars */}
            <div className="p-6 rounded-xl bg-slate-800/30 border border-slate-700/40">
              <h4 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-cyan-400" />
                Airtime Distribution Breakdown
              </h4>

              {/* Progress Stack Bar */}
              <div className="w-full h-4 rounded-full overflow-hidden flex bg-slate-700/50 mb-6">
                {data.participants.map((p, idx) => {
                  const colors = ['bg-cyan-500', 'bg-violet-500', 'bg-emerald-500', 'bg-amber-500'];
                  return (
                    <div
                      key={p.userId}
                      style={{ width: `${p.talkTimePercentage}%` }}
                      className={`${colors[idx % colors.length]} transition-all duration-500`}
                      title={`${p.displayName}: ${p.talkTimePercentage}%`}
                    />
                  );
                })}
              </div>

              {/* List Breakdown */}
              <div className="space-y-3">
                {data.participants.map((p) => (
                  <div key={p.userId} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60 last:border-0">
                    <span className="font-medium text-slate-200">{p.displayName}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-slate-400">{formatSec(p.talkTimeSec)}</span>
                      <span className="font-bold text-cyan-400 w-12 text-right">{p.talkTimePercentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'participants' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.participants.map((p) => (
              <div key={p.userId} className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/40 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-white">{p.displayName}</h4>
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/20 text-cyan-300">
                    {p.averageWpm} WPM
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded bg-slate-900/60">
                    <span className="text-slate-400 block text-[10px]">Total Turns</span>
                    <span className="font-semibold text-slate-200">{p.turnCount}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/60">
                    <span className="text-slate-400 block text-[10px]">Monologues</span>
                    <span className="font-semibold text-slate-200">{p.monologueCount}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/60">
                    <span className="text-slate-400 block text-[10px]">Interruptions Made</span>
                    <span className="font-semibold text-slate-200">{p.interruptionsInitiated}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900/60">
                    <span className="text-slate-400 block text-[10px]">Sentiment</span>
                    <span className="font-semibold text-emerald-400">+{(p.sentimentScore * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/40 border border-slate-700/40">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-slate-300 leading-relaxed">{rec}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
