import React, { useState, useCallback } from 'react';

interface BreakoutRoom {
  id: string;
  name: string;
  participants: Participant[];
  maxCapacity: number;
  isOpen: boolean;
  topic?: string;
  durationMinutes: number;
  remainingSeconds: number;
}

interface Participant {
  id: string;
  displayName: string;
  avatarUrl?: string;
  isHost: boolean;
  currentRoomId?: string;
}

interface BreakoutRoomOrchestratorProps {
  mainRoomCode: string;
  participants: Participant[];
  onCreateRooms?: (numRooms: number, durationMinutes: number) => void;
  onAssignParticipant?: (participantId: string, roomId: string) => void;
  onEndRoom?: (roomId: string) => void;
  onEndAll?: () => void;
  onBroadcastMessage?: (message: string) => void;
  className?: string;
}

const PRESET_CONFIGS = [
  { label: '2 Rooms', rooms: 2 },
  { label: '3 Rooms', rooms: 3 },
  { label: '4 Rooms', rooms: 4 },
  { label: '6 Rooms', rooms: 6 },
];

const Avatar: React.FC<{ name: string; size?: number }> = ({ name, size = 28 }) => {
  const initials = name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
  const colors = ['#4f46e5', '#0891b2', '#059669', '#dc2626', '#d97706', '#7c3aed'];
  const color = colors[name.charCodeAt(0) % colors.length];
  return (
    <div style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: size * 0.35,
      fontWeight: 700,
      flexShrink: 0,
    }}>
      {initials}
    </div>
  );
};

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

const RoomCard: React.FC<{
  room: BreakoutRoom;
  allParticipants: Participant[];
  onAssign: (pid: string, rid: string) => void;
  onEnd: (rid: string) => void;
}> = ({ room, allParticipants, onAssign, onEnd }) => {
  const [expanded, setExpanded] = useState(false);
  const unassigned = allParticipants.filter(p => !p.currentRoomId);
  const timeColor = room.remainingSeconds < 120 ? '#ef4444' : '#22c55e';

  return (
    <div style={{
      border: `1px solid ${room.isOpen ? '#334155' : '#1e293b'}`,
      borderRadius: 12,
      background: room.isOpen ? '#0f172a' : '#0a0f1a',
      marginBottom: 12,
      overflow: 'hidden',
    }}>
      {/* Room header */}
      <div style={{
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        cursor: 'pointer',
      }} onClick={() => setExpanded(e => !e)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 16 }}>{room.isOpen ? '🟢' : '🔴'}</span>
          <div>
            <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 14 }}>{room.name}</div>
            {room.topic && (
              <div style={{ fontSize: 11, color: '#64748b' }}>{room.topic}</div>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            {room.participants.length}/{room.maxCapacity} participants
          </span>
          <span style={{ fontSize: 12, color: timeColor, fontWeight: 600 }}>
            ⏱ {formatTime(room.remainingSeconds)}
          </span>
          <span style={{ color: '#475569', fontSize: 12 }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid #1e293b', padding: '12px 16px' }}>
          {/* Participant list */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 6, fontWeight: 600 }}>
              IN THIS ROOM
            </div>
            {room.participants.length === 0 ? (
              <div style={{ color: '#475569', fontSize: 12, fontStyle: 'italic' }}>Empty</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {room.participants.map(p => (
                  <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Avatar name={p.displayName} size={24} />
                    <span style={{ fontSize: 12, color: '#e2e8f0' }}>{p.displayName}</span>
                    {p.isHost && (
                      <span style={{
                        fontSize: 9, background: '#4f46e520', color: '#818cf8',
                        borderRadius: 4, padding: '1px 5px', fontWeight: 600,
                      }}>HOST</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add participant */}
          {unassigned.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 6, fontWeight: 600 }}>
                MOVE TO ROOM
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {unassigned.map(p => (
                  <button
                    key={p.id}
                    onClick={() => onAssign(p.id, room.id)}
                    style={{
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: 6,
                      color: '#94a3b8',
                      fontSize: 11,
                      padding: '3px 8px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                  >
                    + {p.displayName}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* End room */}
          <button
            onClick={() => onEnd(room.id)}
            style={{
              background: '#7f1d1d20',
              border: '1px solid #991b1b',
              borderRadius: 6,
              color: '#f87171',
              fontSize: 11,
              padding: '5px 12px',
              cursor: 'pointer',
            }}
          >
            End Room
          </button>
        </div>
      )}
    </div>
  );
};

const BreakoutRoomOrchestrator: React.FC<BreakoutRoomOrchestratorProps> = ({
  mainRoomCode,
  participants,
  onCreateRooms,
  onAssignParticipant,
  onEndRoom,
  onEndAll,
  onBroadcastMessage,
  className = '',
}) => {
  const [rooms, setRooms] = useState<BreakoutRoom[]>([]);
  const [numRooms, setNumRooms] = useState(2);
  const [duration, setDuration] = useState(15);
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [assignMode, setAssignMode] = useState<'auto' | 'manual'>('auto');

  const handleCreateRooms = useCallback(() => {
    const newRooms: BreakoutRoom[] = Array.from({ length: numRooms }, (_, i) => {
      const roomParticipants =
        assignMode === 'auto'
          ? participants.filter((_, idx) => idx % numRooms === i)
          : [];
      return {
        id: `room_${i + 1}`,
        name: `Room ${i + 1}`,
        participants: roomParticipants,
        maxCapacity: Math.ceil(participants.length / numRooms) + 2,
        isOpen: true,
        durationMinutes: duration,
        remainingSeconds: duration * 60,
      };
    });
    setRooms(newRooms);
    onCreateRooms?.(numRooms, duration);
  }, [numRooms, duration, participants, assignMode, onCreateRooms]);

  const handleAssign = useCallback((participantId: string, roomId: string) => {
    setRooms(prev =>
      prev.map(room => ({
        ...room,
        participants:
          room.id === roomId
            ? [...room.participants, participants.find(p => p.id === participantId)!].filter(Boolean)
            : room.participants.filter(p => p.id !== participantId),
      }))
    );
    onAssignParticipant?.(participantId, roomId);
  }, [participants, onAssignParticipant]);

  const handleEndRoom = useCallback((roomId: string) => {
    setRooms(prev => prev.map(r => r.id === roomId ? { ...r, isOpen: false } : r));
    onEndRoom?.(roomId);
  }, [onEndRoom]);

  const handleEndAll = useCallback(() => {
    setRooms([]);
    onEndAll?.();
  }, [onEndAll]);

  const handleBroadcast = useCallback(() => {
    if (broadcastMsg.trim()) {
      onBroadcastMessage?.(broadcastMsg);
      setBroadcastMsg('');
      setShowBroadcast(false);
    }
  }, [broadcastMsg, onBroadcastMessage]);

  const totalAssigned = rooms.reduce((sum, r) => sum + r.participants.length, 0);
  const activeRooms = rooms.filter(r => r.isOpen).length;

  return (
    <div className={`breakout-room-orchestrator ${className}`} style={{ fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ padding: '16px 20px', background: '#0f172a', borderRadius: 16 }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: 16, fontWeight: 700 }}>
              🏠 Breakout Rooms
            </h3>
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
              Room: {mainRoomCode} • {participants.length} participants
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {rooms.length > 0 && (
              <>
                <button
                  onClick={() => setShowBroadcast(s => !s)}
                  style={{
                    background: '#1e3a5f',
                    border: '1px solid #1e40af',
                    borderRadius: 8,
                    color: '#60a5fa',
                    fontSize: 12,
                    padding: '6px 12px',
                    cursor: 'pointer',
                  }}
                >
                  📢 Broadcast
                </button>
                <button
                  onClick={handleEndAll}
                  style={{
                    background: '#7f1d1d20',
                    border: '1px solid #991b1b',
                    borderRadius: 8,
                    color: '#f87171',
                    fontSize: 12,
                    padding: '6px 12px',
                    cursor: 'pointer',
                  }}
                >
                  End All
                </button>
              </>
            )}
          </div>
        </div>

        {/* Status */}
        {rooms.length > 0 && (
          <div style={{
            display: 'flex',
            gap: 16,
            marginBottom: 16,
            padding: '10px 14px',
            background: '#1e293b',
            borderRadius: 10,
            fontSize: 12,
          }}>
            <div><span style={{ color: '#64748b' }}>Active Rooms: </span><span style={{ color: '#818cf8', fontWeight: 600 }}>{activeRooms}</span></div>
            <div><span style={{ color: '#64748b' }}>Assigned: </span><span style={{ color: '#22c55e', fontWeight: 600 }}>{totalAssigned}</span></div>
            <div><span style={{ color: '#64748b' }}>Unassigned: </span><span style={{ color: '#f59e0b', fontWeight: 600 }}>{participants.length - totalAssigned}</span></div>
          </div>
        )}

        {/* Broadcast panel */}
        {showBroadcast && (
          <div style={{ marginBottom: 16, padding: '12px 14px', background: '#1e3a5f', borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: '#93c5fd', marginBottom: 8, fontWeight: 600 }}>
              Broadcast to all rooms
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                value={broadcastMsg}
                onChange={e => setBroadcastMsg(e.target.value)}
                placeholder="Type a message…"
                style={{
                  flex: 1,
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: 6,
                  color: '#f1f5f9',
                  fontSize: 12,
                  padding: '6px 10px',
                  outline: 'none',
                }}
              />
              <button
                onClick={handleBroadcast}
                style={{
                  background: '#1d4ed8',
                  border: 'none',
                  borderRadius: 6,
                  color: '#fff',
                  fontSize: 12,
                  padding: '6px 14px',
                  cursor: 'pointer',
                }}
              >
                Send
              </button>
            </div>
          </div>
        )}

        {/* Configuration (when no rooms yet) */}
        {rooms.length === 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10, fontWeight: 600 }}>
              CONFIGURE BREAKOUTS
            </div>

            {/* Preset room counts */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              {PRESET_CONFIGS.map(cfg => (
                <button
                  key={cfg.rooms}
                  onClick={() => setNumRooms(cfg.rooms)}
                  style={{
                    background: numRooms === cfg.rooms ? '#4f46e5' : '#1e293b',
                    border: `1px solid ${numRooms === cfg.rooms ? '#6366f1' : '#334155'}`,
                    borderRadius: 8,
                    color: numRooms === cfg.rooms ? '#fff' : '#94a3b8',
                    fontSize: 12,
                    padding: '6px 12px',
                    cursor: 'pointer',
                    fontWeight: numRooms === cfg.rooms ? 600 : 400,
                  }}
                >
                  {cfg.label}
                </button>
              ))}
            </div>

            {/* Duration */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{ fontSize: 12, color: '#64748b', width: 80 }}>Duration</span>
              {[10, 15, 20, 30, 45].map(min => (
                <button
                  key={min}
                  onClick={() => setDuration(min)}
                  style={{
                    background: duration === min ? '#0891b2' : '#1e293b',
                    border: `1px solid ${duration === min ? '#06b6d4' : '#334155'}`,
                    borderRadius: 8,
                    color: duration === min ? '#fff' : '#94a3b8',
                    fontSize: 11,
                    padding: '4px 10px',
                    cursor: 'pointer',
                  }}
                >
                  {min}m
                </button>
              ))}
            </div>

            {/* Assignment mode */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <span style={{ fontSize: 12, color: '#64748b', width: 80 }}>Assign</span>
              {(['auto', 'manual'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => setAssignMode(mode)}
                  style={{
                    background: assignMode === mode ? '#059669' : '#1e293b',
                    border: `1px solid ${assignMode === mode ? '#10b981' : '#334155'}`,
                    borderRadius: 8,
                    color: assignMode === mode ? '#fff' : '#94a3b8',
                    fontSize: 11,
                    padding: '4px 12px',
                    cursor: 'pointer',
                  }}
                >
                  {mode === 'auto' ? 'Auto' : 'Manual'}
                </button>
              ))}
            </div>

            <button
              onClick={handleCreateRooms}
              disabled={participants.length === 0}
              style={{
                background: participants.length === 0 ? '#1e293b' : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                border: 'none',
                borderRadius: 10,
                color: participants.length === 0 ? '#475569' : '#fff',
                fontSize: 13,
                fontWeight: 600,
                padding: '10px 24px',
                cursor: participants.length === 0 ? 'not-allowed' : 'pointer',
                width: '100%',
              }}
            >
              Create {numRooms} Breakout Rooms → {duration}min each
            </button>
          </div>
        )}

        {/* Room cards */}
        {rooms.map(room => (
          <RoomCard
            key={room.id}
            room={room}
            allParticipants={participants}
            onAssign={handleAssign}
            onEnd={handleEndRoom}
          />
        ))}
      </div>
    </div>
  );
};

export default BreakoutRoomOrchestrator;
