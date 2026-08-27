import React, { useState, useEffect, useCallback } from 'react';
import { X, Users, Play, Square, MessageSquare, Clock, ArrowRight } from 'lucide-react';
import client from '../../api/client';
import type { BreakoutRoomItem } from '../../types/collaboration';

export interface BreakoutRoomsModalProps {
  isOpen: boolean;
  onClose: () => void;
  roomCode: string;
}

export const BreakoutRoomsModal: React.FC<BreakoutRoomsModalProps> = ({
  isOpen,
  onClose,
  roomCode,
}) => {
  const [numRooms, setNumRooms] = useState<number>(2);
  const [duration, setDuration] = useState<number>(15);
  const [breakoutRooms, setBreakoutRooms] = useState<BreakoutRoomItem[]>([]);
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchBreakoutRooms = useCallback(async () => {
    try {
      setLoading(true);
      const res = await client.get<BreakoutRoomItem[]>(`/api/breakout/meeting/${roomCode}`);
      setBreakoutRooms(res.data);
    } catch (err) {
      console.warn('Failed to fetch breakout rooms:', err);
    } finally {
      setLoading(false);
    }
  }, [roomCode]);

  useEffect(() => {
    if (isOpen) {
      fetchBreakoutRooms();
    }
  }, [isOpen, fetchBreakoutRooms]);

  if (!isOpen) return null;

  const handleCreateRooms = async () => {
    try {
      setLoading(true);
      const res = await client.post('/api/breakout/create', {
        meeting_code: roomCode,
        num_rooms: numRooms,
        duration_minutes: duration,
        auto_assign: true,
      });
      setBreakoutRooms(res.data);
    } catch (err) {
      console.warn('Failed creating breakout rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseRooms = async () => {
    try {
      setLoading(true);
      await client.post('/api/breakout/close', {
        meeting_code: roomCode,
      });
      setBreakoutRooms([]);
    } catch (err) {
      console.warn('Failed closing breakout rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl rounded-3xl glass-card border border-white/10 bg-[#0c0e1a]/95 p-6 text-white shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-amber-500/20 border border-amber-500/30 text-amber-400">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Breakout Rooms</h2>
              <p className="text-xs text-gray-400">Split participants into smaller focused sub-rooms</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {breakoutRooms.length === 0 ? (
          /* Create Rooms Form */
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                  Number of Sub-Rooms
                </label>
                <select
                  value={numRooms}
                  onChange={(e) => setNumRooms(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                >
                  <option value={2} className="bg-[#0c0e1a]">2 Breakout Rooms</option>
                  <option value={3} className="bg-[#0c0e1a]">3 Breakout Rooms</option>
                  <option value={4} className="bg-[#0c0e1a]">4 Breakout Rooms</option>
                  <option value={5} className="bg-[#0c0e1a]">5 Breakout Rooms</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                  Timer Duration
                </label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-amber-500 text-sm"
                >
                  <option value={10} className="bg-[#0c0e1a]">10 Minutes</option>
                  <option value={15} className="bg-[#0c0e1a]">15 Minutes</option>
                  <option value={30} className="bg-[#0c0e1a]">30 Minutes</option>
                </select>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-3">
              <Clock className="w-5 h-5 flex-shrink-0" />
              <span>Participants will be automatically distributed into breakout sub-rooms upon creation.</span>
            </div>

            <div className="pt-4 border-t border-white/10 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 font-semibold text-xs cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateRooms}
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-amber-500/30 cursor-pointer"
              >
                <Play className="w-4 h-4 fill-slate-950" /> Start Breakout Rooms
              </button>
            </div>
          </div>
        ) : (
          /* Active Rooms Control Panel */
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
              <span>{breakoutRooms.length} Breakout Sub-Rooms Active</span>
              <button
                onClick={handleCloseRooms}
                className="px-3 py-1.5 rounded-lg bg-rose-500/30 hover:bg-rose-500/50 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center gap-1 cursor-pointer"
              >
                <Square className="w-3.5 h-3.5 fill-rose-300" /> End All Sub-Rooms
              </button>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {breakoutRooms.map((room) => (
                <div key={room.id} className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">{room.room_name}</h4>
                    <span className="text-xs text-gray-400">{room.assigned_users.length} Participants Assigned</span>
                  </div>

                  <a
                    href={`/room/${roomCode}-${room.id.substring(0, 4)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    Jump To Room <ArrowRight className="w-3.5 h-3.5" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BreakoutRoomsModal;
