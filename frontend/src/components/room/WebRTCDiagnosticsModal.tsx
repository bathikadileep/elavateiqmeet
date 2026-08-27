import React from 'react';
import { X, Activity, Wifi, ShieldCheck, Cpu, Signal, Layers } from 'lucide-react';
import type { WebRTCHealthMetrics } from '../../types/sfu';

export interface WebRTCDiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  metrics: WebRTCHealthMetrics;
  sfuActive: boolean;
  participantCount: number;
}

export const WebRTCDiagnosticsModal: React.FC<WebRTCDiagnosticsModalProps> = ({
  isOpen,
  onClose,
  metrics,
  sfuActive,
  participantCount,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-3xl glass-card border border-white/10 bg-[#0c0e1a]/90 p-6 text-white shadow-2xl overflow-hidden">
        {/* Ambient Glow background element */}
        <div className="absolute -top-20 -right-20 w-60 h-60 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                WebRTC Network & SFU Diagnostics
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {sfuActive ? 'SFU Engine Active' : 'P2P Mesh Mode'}
                </span>
              </h2>
              <p className="text-xs text-gray-400">Real-time media transport health & stream statistics</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Health Score Summary Banner */}
        <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/40 to-blue-900/40 border border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold block">Quality Score</span>
              <span className="text-3xl font-black text-emerald-400">{metrics.score} <span className="text-sm font-normal text-gray-400">/ 10</span></span>
            </div>
            <div className="h-10 w-px bg-white/10" />
            <div>
              <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold block">Active Simulcast Layer</span>
              <span className="text-base font-bold text-indigo-300 flex items-center gap-1.5 mt-0.5">
                <Layers className="w-4 h-4 text-indigo-400" />
                {metrics.simulcastLayer.toUpperCase()} ({metrics.resolution} @ {metrics.framerateFps}fps)
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold block">Active Peers</span>
            <span className="text-xl font-bold text-white mt-0.5">{participantCount} Participants</span>
          </div>
        </div>

        {/* Metrics Grid Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {/* Card 1: RTT Latency */}
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between">
            <div className="flex items-center justify-between text-gray-400 text-xs font-semibold mb-2">
              <span>RTT Latency</span>
              <Wifi className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">{metrics.rttMs} <span className="text-xs text-gray-400 font-normal">ms</span></div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className={`h-full rounded-full ${metrics.rttMs < 100 ? 'bg-emerald-400' : metrics.rttMs < 250 ? 'bg-amber-400' : 'bg-rose-400'}`}
                style={{ width: `${Math.min(100, (metrics.rttMs / 300) * 100)}%` }}
              />
            </div>
          </div>

          {/* Card 2: Packet Loss */}
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between">
            <div className="flex items-center justify-between text-gray-400 text-xs font-semibold mb-2">
              <span>Packet Loss</span>
              <Signal className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-white">{metrics.packetLossPercent}%</div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className={`h-full rounded-full ${metrics.packetLossPercent < 1 ? 'bg-emerald-400' : metrics.packetLossPercent < 4 ? 'bg-amber-400' : 'bg-rose-400'}`}
                style={{ width: `${Math.min(100, (metrics.packetLossPercent / 10) * 100)}%` }}
              />
            </div>
          </div>

          {/* Card 3: Video Bitrate */}
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between">
            <div className="flex items-center justify-between text-gray-400 text-xs font-semibold mb-2">
              <span>Video Bitrate</span>
              <Cpu className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white">{metrics.videoBitrateKbps} <span className="text-xs text-gray-400 font-normal">kbps</span></div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="h-full bg-purple-400 rounded-full"
                style={{ width: `${Math.min(100, (metrics.videoBitrateKbps / 2000) * 100)}%` }}
              />
            </div>
          </div>

          {/* Card 4: Audio Bitrate */}
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between">
            <div className="flex items-center justify-between text-gray-400 text-xs font-semibold mb-2">
              <span>Audio Bitrate</span>
              <ShieldCheck className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">{metrics.audioBitrateKbps} <span className="text-xs text-gray-400 font-normal">kbps</span></div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="h-full bg-blue-400 rounded-full"
                style={{ width: `${Math.min(100, (metrics.audioBitrateKbps / 128) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Real-time Health Chart Simulation */}
        <div className="p-4 rounded-2xl bg-white/5 border border-white/10 mb-4">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-300 mb-3">
            <span>Bitrate & Latency Real-time Flow</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" /> Live Sampling
            </span>
          </div>

          <svg className="w-full h-20 overflow-visible" viewBox="0 0 400 80">
            <path
              d="M 0,60 Q 50,40 100,50 T 200,30 T 300,45 T 400,20"
              fill="none"
              stroke="#818cf8"
              strokeWidth="2.5"
            />
            <path
              d="M 0,60 Q 50,40 100,50 T 200,30 T 300,45 T 400,20 L 400,80 L 0,80 Z"
              fill="url(#grad)"
              opacity="0.15"
            />
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#818cf8" />
                <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-white/10 text-xs text-gray-400">
          <span>Opus Audio @ 48kHz | VP8 / H.264 Video Simulcast</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors cursor-pointer shadow-lg shadow-indigo-600/30"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default WebRTCDiagnosticsModal;
