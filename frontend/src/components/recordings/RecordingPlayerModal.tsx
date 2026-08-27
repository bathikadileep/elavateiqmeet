import React, { useState } from 'react';
import { X, Play, Pause, Download, Video, Search, Volume2 } from 'lucide-react';
import type { MeetingRecordingItem } from '../../types/recordings';

export interface RecordingPlayerModalProps {
  recording: MeetingRecordingItem | null;
  isOpen: boolean;
  onClose: () => void;
}

export const RecordingPlayerModal: React.FC<RecordingPlayerModalProps> = ({
  recording,
  isOpen,
  onClose,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen || !recording) return null;

  const streamUrl = recording.hls_playlist_url || `/api/recordings/${recording.id}/stream/index.m3u8`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-4xl rounded-3xl glass-card border border-white/10 bg-[#080911]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-400">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">HLS Cloud Video Player</h2>
              <p className="text-xs text-gray-400">
                Recording ID: {recording.id} • {recording.duration_seconds || 30}s Duration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={recording.download_url || '#'}
              download
              className="px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-lg shadow-cyan-600/30 cursor-pointer"
            >
              <Download className="w-4 h-4" /> Download Video
            </a>

            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Video Player Box */}
        <div className="relative w-full aspect-video rounded-2xl bg-black border border-white/10 overflow-hidden flex items-center justify-center group mb-4">
          <video
            controls
            src={streamUrl}
            className="w-full h-full object-contain"
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />

          {!isPlaying && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center pointer-events-none">
              <div className="p-5 rounded-full bg-cyan-500/80 text-white shadow-2xl backdrop-blur-md">
                <Play className="w-10 h-10 fill-white translate-x-0.5" />
              </div>
            </div>
          )}
        </div>

        {/* Controls & Transcript Search Bar */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10 text-xs">
          <div className="flex items-center gap-3">
            <span className="text-gray-400 font-semibold">Speed:</span>
            {[0.75, 1, 1.25, 1.5, 2].map((s) => (
              <button
                key={s}
                onClick={() => setPlaybackSpeed(s)}
                className={`px-2.5 py-1 rounded-lg transition-colors font-bold ${
                  playbackSpeed === s ? 'bg-cyan-500 text-white' : 'bg-white/5 text-gray-300 hover:bg-white/10'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in transcript..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecordingPlayerModal;
