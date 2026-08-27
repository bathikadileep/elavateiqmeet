import React, { useState, useEffect, useCallback } from 'react';
import { X, Video, Play, HardDrive, Clock, FileVideo } from 'lucide-react';
import client from '../../api/client';
import type { MeetingRecordingItem } from '../../types/recordings';
import RecordingPlayerModal from './RecordingPlayerModal';

export interface RecordingsListModalProps {
  isOpen: boolean;
  onClose: () => void;
  roomCode: string;
}

export const RecordingsListModal: React.FC<RecordingsListModalProps> = ({
  isOpen,
  onClose,
  roomCode,
}) => {
  const [recordings, setRecordings] = useState<MeetingRecordingItem[]>([]);
  const [activeRecording, setActiveRecording] = useState<MeetingRecordingItem | null>(null);
  const [playerOpen, setPlayerOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchRecordings = useCallback(async () => {
    try {
      setLoading(true);
      const res = await client.get<MeetingRecordingItem[]>(`/api/recordings/meeting/${roomCode}`);
      setRecordings(res.data);
    } catch (err) {
      console.warn('Failed fetching recordings:', err);
    } finally {
      setLoading(false);
    }
  }, [roomCode]);

  useEffect(() => {
    if (isOpen) {
      fetchRecordings();
    }
  }, [isOpen, fetchRecordings]);

  if (!isOpen) return null;

  const handlePlay = (rec: MeetingRecordingItem) => {
    setActiveRecording(rec);
    setPlayerOpen(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl max-h-[85vh] rounded-3xl glass-card border border-white/10 bg-[#0c0e1a]/95 p-6 text-white shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-rose-500/20 border border-rose-500/30 text-rose-400">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Cloud Recordings Library</h2>
              <p className="text-xs text-gray-400">HLS video playback & pluggable storage archives</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Recordings List */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-3">
          {loading ? (
            <div className="text-center py-12 text-sm text-gray-400">Loading cloud recordings...</div>
          ) : recordings.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <FileVideo className="w-12 h-12 text-gray-600 mx-auto mb-2" />
              <p className="text-sm font-semibold">No recordings found</p>
              <p className="text-xs text-gray-500 mt-1">Start recording during a call to save meeting sessions</p>
            </div>
          ) : (
            recordings.map((rec) => (
              <div
                key={rec.id}
                className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between hover:border-white/20 transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-rose-500/20 text-rose-400">
                    <FileVideo className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Meeting Session Recording</h4>
                    <div className="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" /> {rec.duration_seconds || 30}s
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="w-3.5 h-3.5" /> {Math.round((rec.size_bytes || 1024) / 1024)} KB
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handlePlay(rec)}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center gap-1.5 shadow-lg shadow-cyan-600/30 cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-white" /> Watch HLS
                </button>
              </div>
            ))
          )}
        </div>

        <RecordingPlayerModal
          recording={activeRecording}
          isOpen={playerOpen}
          onClose={() => setPlayerOpen(false)}
        />
      </div>
    </div>
  );
};

export default RecordingsListModal;
