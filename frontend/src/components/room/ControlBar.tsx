import { Mic, MicOff, Video as VideoIcon, VideoOff, Monitor, MessageSquare, Hand, PhoneOff, Activity, Edit3, Vote, Users, Subtitles, Sparkles, Bot, Disc, Film, ShieldCheck, Code } from 'lucide-react';

export interface ControlBarProps {
  isAudioMuted: boolean;
  isVideoOff: boolean;
  isScreenSharing: boolean;
  handRaised: boolean;
  chatOpen: boolean;
  participantCount: number;
  subtitlesEnabled?: boolean;
  isRecording?: boolean;
  isE2EEEnabled?: boolean;
  onToggleAudio: () => void;
  onToggleVideo: () => void;
  onToggleScreenShare: () => void;
  onToggleHandRaise: () => void;
  onToggleChat: () => void;
  onLeave: () => void;
  onOpenDiagnostics?: () => void;
  onOpenWhiteboard?: () => void;
  onOpenPolls?: () => void;
  onOpenBreakout?: () => void;
  onToggleSubtitles?: () => void;
  onOpenVirtualBackground?: () => void;
  onOpenAISummary?: () => void;
  onToggleRecording?: () => void;
  onOpenRecordingsLibrary?: () => void;
  onOpenSecurityAudit?: () => void;
  onOpenDeveloperPortal?: () => void;
}

export const ControlBar: React.FC<ControlBarProps> = ({
  isAudioMuted,
  isVideoOff,
  isScreenSharing,
  handRaised,
  chatOpen,
  participantCount,
  subtitlesEnabled = false,
  isRecording = false,
  isE2EEEnabled = false,
  onToggleAudio,
  onToggleVideo,
  onToggleScreenShare,
  onToggleHandRaise,
  onToggleChat,
  onLeave,
  onOpenDiagnostics,
  onOpenWhiteboard,
  onOpenPolls,
  onOpenBreakout,
  onToggleSubtitles,
  onOpenVirtualBackground,
  onOpenAISummary,
  onToggleRecording,
  onOpenRecordingsLibrary,
  onOpenSecurityAudit,
  onOpenDeveloperPortal,
}) => {
  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40 px-6 py-3 rounded-2xl glass-card border border-white/10 bg-[#080911]/85 backdrop-blur-2xl shadow-2xl flex items-center gap-3">
      {/* Mic Mute Button */}
      <button
        onClick={onToggleAudio}
        title={isAudioMuted ? 'Unmute Microphone' : 'Mute Microphone'}
        className={`p-3.5 rounded-xl transition-all cursor-pointer ${
          isAudioMuted
            ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
        }`}
      >
        {isAudioMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
      </button>

      {/* Video Camera Button */}
      <button
        onClick={onToggleVideo}
        title={isVideoOff ? 'Turn Camera On' : 'Turn Camera Off'}
        className={`p-3.5 rounded-xl transition-all cursor-pointer ${
          isVideoOff
            ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
        }`}
      >
        {isVideoOff ? <VideoOff className="w-5 h-5" /> : <VideoIcon className="w-5 h-5" />}
      </button>

      {/* Screen Share Button */}
      <button
        onClick={onToggleScreenShare}
        title={isScreenSharing ? 'Stop Screen Sharing' : 'Share Screen'}
        className={`p-3.5 rounded-xl transition-all cursor-pointer ${
          isScreenSharing
            ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
        }`}
      >
        <Monitor className="w-5 h-5" />
      </button>

      <div className="h-6 w-px bg-white/10 mx-1" />

      {/* Interactive Whiteboard Toggle */}
      {onOpenWhiteboard && (
        <button
          onClick={onOpenWhiteboard}
          title="Open Interactive Whiteboard"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-indigo-400 border border-white/10 cursor-pointer"
        >
          <Edit3 className="w-5 h-5" />
        </button>
      )}

      {/* In-Meeting Live Polls Toggle */}
      {onOpenPolls && (
        <button
          onClick={onOpenPolls}
          title="Open Live Polls"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-purple-400 border border-white/10 cursor-pointer"
        >
          <Vote className="w-5 h-5" />
        </button>
      )}

      {/* Breakout Rooms Toggle */}
      {onOpenBreakout && (
        <button
          onClick={onOpenBreakout}
          title="Manage Breakout Rooms"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-amber-400 border border-white/10 cursor-pointer"
        >
          <Users className="w-5 h-5" />
        </button>
      )}

      {/* Live Subtitles (CC) Toggle */}
      {onToggleSubtitles && (
        <button
          onClick={onToggleSubtitles}
          title={subtitlesEnabled ? 'Turn Off Subtitles' : 'Turn On Live Subtitles'}
          className={`p-3.5 rounded-xl transition-all cursor-pointer ${
            subtitlesEnabled
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
              : 'bg-white/10 hover:bg-white/20 text-blue-400 border border-white/10'
          }`}
        >
          <Subtitles className="w-5 h-5" />
        </button>
      )}

      {/* Virtual Background Studio Toggle */}
      {onOpenVirtualBackground && (
        <button
          onClick={onOpenVirtualBackground}
          title="Virtual Studio & Background Blur"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-pink-400 border border-white/10 cursor-pointer"
        >
          <Sparkles className="w-5 h-5" />
        </button>
      )}

      {/* AI Assistant Summary Toggle */}
      {onOpenAISummary && (
        <button
          onClick={onOpenAISummary}
          title="AI Meeting Assistant Summary"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-cyan-400 border border-white/10 cursor-pointer"
        >
          <Bot className="w-5 h-5" />
        </button>
      )}

      {/* Cloud Recording Toggle */}
      {onToggleRecording && (
        <button
          onClick={onToggleRecording}
          title={isRecording ? 'Stop Cloud Recording' : 'Start Cloud Recording'}
          className={`p-3.5 rounded-xl transition-all cursor-pointer ${
            isRecording
              ? 'bg-red-600 text-white shadow-lg shadow-red-500/40 animate-pulse'
              : 'bg-white/10 hover:bg-white/20 text-red-400 border border-white/10'
          }`}
        >
          <Disc className="w-5 h-5" />
        </button>
      )}

      {/* Recordings Library Toggle */}
      {onOpenRecordingsLibrary && (
        <button
          onClick={onOpenRecordingsLibrary}
          title="Cloud Recordings Library"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-rose-400 border border-white/10 cursor-pointer"
        >
          <Film className="w-5 h-5" />
        </button>
      )}

      {/* Enterprise Security Audit Toggle */}
      {onOpenSecurityAudit && (
        <button
          onClick={onOpenSecurityAudit}
          title="Enterprise Security & SOC2 Governance"
          className={`p-3.5 rounded-xl transition-all cursor-pointer ${
            isE2EEEnabled
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30'
              : 'bg-white/10 hover:bg-white/20 text-emerald-400 border border-white/10'
          }`}
        >
          <ShieldCheck className="w-5 h-5" />
        </button>
      )}

      {/* Developer API Gateway & Webhooks Toggle */}
      {onOpenDeveloperPortal && (
        <button
          onClick={onOpenDeveloperPortal}
          title="Developer API Gateway & Webhook Marketplace"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-cyan-400 border border-white/10 cursor-pointer"
        >
          <Code className="w-5 h-5" />
        </button>
      )}

      <div className="h-6 w-px bg-white/10 mx-1" />

      {/* Hand Raise Button */}
      <button
        onClick={onToggleHandRaise}
        title={handRaised ? 'Lower Hand' : 'Raise Hand'}
        className={`p-3.5 rounded-xl transition-all cursor-pointer ${
          handRaised
            ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
        }`}
      >
        <Hand className="w-5 h-5" />
      </button>

      {/* Chat Drawer Toggle */}
      <button
        onClick={onToggleChat}
        title="Toggle Chat Drawer"
        className={`p-3.5 rounded-xl transition-all relative cursor-pointer ${
          chatOpen
            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
            : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'
        }`}
      >
        <MessageSquare className="w-5 h-5" />
        <span className="absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full bg-indigo-500 text-[10px] font-bold text-white shadow">
          {participantCount}
        </span>
      </button>

      {/* WebRTC Diagnostics HUD Toggle */}
      {onOpenDiagnostics && (
        <button
          onClick={onOpenDiagnostics}
          title="Network & SFU Diagnostics HUD"
          className="p-3.5 rounded-xl transition-all bg-white/10 hover:bg-white/20 text-emerald-400 border border-white/10 cursor-pointer"
        >
          <Activity className="w-5 h-5" />
        </button>
      )}

      <div className="h-6 w-px bg-white/10 mx-1" />

      {/* Leave Room Button */}
      <button
        onClick={onLeave}
        title="Leave Meeting"
        className="p-3.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white shadow-lg shadow-rose-600/30 font-bold flex items-center gap-2 transition-all cursor-pointer px-5"
      >
        <PhoneOff className="w-5 h-5" />
        <span className="text-xs tracking-wide uppercase hidden sm:inline-block">End Call</span>
      </button>
    </div>
  );
};

export default ControlBar;
