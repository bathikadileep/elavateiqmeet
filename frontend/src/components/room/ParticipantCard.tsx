import React, { useEffect, useRef } from 'react';
import Avatar from '../common/Avatar';
import Badge from '../common/Badge';
import { Mic, MicOff, Monitor, Hand } from 'lucide-react';
import type { PeerStream } from '../../types/webrtc';

export interface ParticipantCardProps {
  peer: PeerStream;
  isSpeaking?: boolean;
  simulcastLayer?: 'high' | 'medium' | 'low';
}

export const ParticipantCard: React.FC<ParticipantCardProps> = ({ peer, isSpeaking = false, simulcastLayer = 'high' }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Attach Stream to Video Element
  useEffect(() => {
    if (videoRef.current && peer.stream) {
      if (videoRef.current.srcObject !== peer.stream) {
        videoRef.current.srcObject = peer.stream;
      }
      videoRef.current.play().catch((err) => {
        console.warn('Video play error for peer:', peer.name, err);
      });
    }
  }, [peer.stream, peer.name]);

  // Attach Stream to Dedicated Audio Element (For Remote Peers) & Handle Autoplay Unlocks
  useEffect(() => {
    if (audioRef.current && peer.stream && !peer.isLocal) {
      if (audioRef.current.srcObject !== peer.stream) {
        audioRef.current.srcObject = peer.stream;
      }
      
      const playAudio = () => {
        if (audioRef.current) {
          audioRef.current.play().catch((err) => {
            console.warn('Audio play error for peer:', peer.name, err);
          });
        }
      };

      playAudio();

      // Autoplay fallback: retry playing audio on first user gesture
      const handleUserGesture = () => {
        playAudio();
        window.removeEventListener('click', handleUserGesture);
      };
      window.addEventListener('click', handleUserGesture);

      return () => {
        window.removeEventListener('click', handleUserGesture);
      };
    }
  }, [peer.stream, peer.isLocal, peer.name]);

  return (
    <div
      className={`relative w-full h-full min-h-[220px] rounded-2xl glass-card border transition-all duration-300 overflow-hidden bg-[#0c0e1a] flex flex-col items-center justify-center group shadow-xl ${
        isSpeaking
          ? 'border-emerald-400 ring-4 ring-emerald-400/30 shadow-emerald-500/20'
          : 'border-white/10 hover:border-white/20'
      }`}
    >
      {/* Dedicated Remote Audio Player */}
      {!peer.isLocal && peer.stream && (
        <audio ref={audioRef} autoPlay playsInline muted={false} />
      )}

      {/* Video Element — Always mounted so video tracks display smoothly */}
      {peer.stream && (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={peer.isLocal} // Mute local preview to prevent echo feedback
          className={`${
            peer.isVideoOff ? 'hidden' : 'w-full h-full object-cover'
          } ${peer.isLocal && !peer.isScreenSharing ? 'scale-x-[-1]' : ''}`}
        />
      )}

      {/* Video Off Fallback Avatar */}
      {peer.isVideoOff && (
        <div className="flex flex-col items-center justify-center gap-3">
          <Avatar name={peer.name} size="xl" />
          <span className="text-sm font-semibold text-gray-300">{peer.name}</span>
        </div>
      )}

      {/* Top Left Badges (Hand Raise & Screen Share & Simulcast Layer) */}
      <div className="absolute top-3 left-3 flex items-center gap-2 z-10">
        {peer.handRaised && (
          <div className="p-2 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-300 animate-bounce flex items-center gap-1 text-xs font-bold shadow-lg">
            <Hand className="w-4 h-4" />
            <span>Hand Raised</span>
          </div>
        )}

        {peer.isScreenSharing && (
          <Badge variant="info" size="sm">
            <Monitor className="w-3.5 h-3.5 mr-1" /> Presenting
          </Badge>
        )}

        {/* Simulcast Quality Layer Badge */}
        {!peer.isLocal && !peer.isVideoOff && (
          <span className="px-2 py-0.5 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-[10px] font-semibold text-indigo-300">
            {simulcastLayer.toUpperCase()}
          </span>
        )}
      </div>

      {/* Bottom Overlay Info Bar */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between z-10">
        <div className="px-3 py-1.5 rounded-xl bg-[#080911]/80 backdrop-blur-md border border-white/10 flex items-center gap-2 text-xs font-medium text-white shadow-md max-w-[80%] truncate">
          <span className="truncate">{peer.name}</span>
        </div>

        {/* Mic Status Badge */}
        <div
          className={`p-2 rounded-xl backdrop-blur-md border shadow-md transition-colors ${
            peer.isAudioMuted
              ? 'bg-rose-500/20 border-rose-500/30 text-rose-400'
              : isSpeaking
              ? 'bg-emerald-500/30 border-emerald-400 text-emerald-300 animate-pulse'
              : 'bg-[#080911]/80 border-white/10 text-emerald-400'
          }`}
        >
          {peer.isAudioMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </div>
      </div>
    </div>
  );
};

export default ParticipantCard;
