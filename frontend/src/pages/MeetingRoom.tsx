import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebRTC } from '../hooks/useWebRTC';
import { useSocket } from '../contexts/SocketContext';
import VideoGrid from '../components/room/VideoGrid';
import MultiStreamVideoCompositor from '../components/room/MultiStreamVideoCompositor';
import ControlBar from '../components/room/ControlBar';
import ChatDrawer from '../components/chat/ChatDrawer';
import Badge from '../components/common/Badge';
import { Video, ShieldCheck, Copy, Check, AlertTriangle, Share2, Layout } from 'lucide-react';

export const MeetingRoom: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const roomCode = code || 'instant-room';

  const {
    allStreams,
    isAudioMuted,
    isVideoOff,
    isScreenSharing,
    handRaised,
    mediaError,
    toggleAudio,
    toggleVideo,
    toggleScreenShare,
    toggleHandRaise,
  } = useWebRTC(roomCode);

  const { onlineUsers } = useSocket();

  const [chatOpen, setChatOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [inviteCopied, setInviteCopied] = useState(false);
  const [sessionSeconds, setSessionSeconds] = useState(0);
  const [useCompositor, setUseCompositor] = useState(true);

  // Session timer
  useEffect(() => {
    const timer = setInterval(() => {
      setSessionSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (totalSec: number) => {
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(roomCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShareInvite = async () => {
    const inviteLink = `${window.location.origin}/room/${roomCode}`;
    const shareText = `Join my ElevateIQ Meet video conference:\nMeeting Code: ${roomCode}\nLink: ${inviteLink}`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'ElevateIQ Meeting Invite',
          text: shareText,
          url: inviteLink,
        });
        return;
      } catch (err) {
        // Fallback to clipboard
      }
    }

    try {
      await navigator.clipboard.writeText(shareText);
      setInviteCopied(true);
      setTimeout(() => setInviteCopied(false), 2500);
    } catch (err) {
      console.warn('Clipboard copy failed:', err);
    }
  };

  const handleLeave = () => {
    navigate('/dashboard');
  };

  return (
    <div className="h-screen w-screen bg-[#080911] text-gray-100 flex flex-col overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      {/* Top Floating Glass Header */}
      <header className="h-16 px-6 bg-[#080911]/70 backdrop-blur-xl border-b border-white/10 flex items-center justify-between z-30 select-none">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Video className="w-5 h-5 text-white" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-extrabold text-white">ElevateIQ Meeting Room</h2>
              <Badge variant="success" size="sm" pulse>
                Encrypted
              </Badge>
            </div>
            <p className="text-[11px] text-gray-400 font-mono">Code: {roomCode}</p>
          </div>

          <button
            onClick={handleCopyCode}
            title="Copy Meeting Code"
            className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer ml-1"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={handleShareInvite}
            title="Share Meeting Link with Participants"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-200 text-xs font-semibold transition-all cursor-pointer shadow-sm ml-1"
          >
            {inviteCopied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5 text-indigo-300" />
                <span className="hidden sm:inline">Invite / Share</span>
              </>
            )}
          </button>
        </div>

        {/* Timer & Security Badge */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setUseCompositor((prev) => !prev)}
            title={useCompositor ? 'Switch to Simple Grid' : 'Switch to Dynamic Compositor'}
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-xs text-indigo-200 transition"
          >
            <Layout className="w-3.5 h-3.5" />
            <span>{useCompositor ? 'Studio Layout' : 'Simple Grid'}</span>
          </button>

          <div className="px-3 py-1.5 rounded-xl glass-card border border-white/10 text-xs font-mono font-bold text-indigo-300">
            {formatTimer(sessionSeconds)}
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>P2P Direct</span>
          </div>
        </div>
      </header>

      {/* Main Canvas + Slide-Over Chat */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Media Warning Banner */}
        {mediaError && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-4 py-2 bg-rose-500/20 border border-rose-500/30 backdrop-blur-md rounded-xl flex items-center gap-2 text-rose-300 text-xs shadow-xl">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{mediaError}</span>
          </div>
        )}

        {/* Video Canvas Grid or Dynamic Compositor */}
        <div className="flex-1 overflow-hidden relative">
          {useCompositor ? (
            <MultiStreamVideoCompositor streams={allStreams} />
          ) : (
            <VideoGrid streams={allStreams} />
          )}
        </div>

        {/* Slide-over Real-Time Chat & Roster Drawer */}
        {chatOpen && <ChatDrawer onClose={() => setChatOpen(false)} />}
      </div>

      {/* Bottom Floating Glass Control Bar */}
      <ControlBar
        isAudioMuted={isAudioMuted}
        isVideoOff={isVideoOff}
        isScreenSharing={isScreenSharing}
        handRaised={handRaised}
        chatOpen={chatOpen}
        participantCount={onlineUsers.length || allStreams.length}
        onToggleAudio={toggleAudio}
        onToggleVideo={toggleVideo}
        onToggleScreenShare={toggleScreenShare}
        onToggleHandRaise={toggleHandRaise}
        onToggleChat={() => setChatOpen(!chatOpen)}
        onLeave={handleLeave}
      />
    </div>
  );
};

export default MeetingRoom;
