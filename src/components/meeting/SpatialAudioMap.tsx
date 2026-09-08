import React, { useState, useEffect, useRef } from 'react';

interface Participant {
  id: string;
  displayName: string;
  isSpeaking: boolean;
  isMuted: boolean;
  position: { x: number; y: number };
}

interface SpatialAudioNode {
  participantId: string;
  displayName: string;
  azimuthDeg: number;
  elevationDeg: number;
  distance: number;
  gainDb: number;
  isSpeaking: boolean;
  isMuted: boolean;
}

interface SpatialAudioMapProps {
  participants: Participant[];
  onPositionChange?: (participantId: string, x: number, y: number) => void;
  roomShape?: 'circle' | 'grid' | 'semicircle';
  className?: string;
}

const ROOM_RADIUS = 160;
const CENTER = 200;
const CANVAS_SIZE = 400;
const AVATAR_RADIUS = 24;

function posToCanvas(x: number, y: number): { cx: number; cy: number } {
  return {
    cx: CENTER + x * ROOM_RADIUS,
    cy: CENTER - y * ROOM_RADIUS,
  };
}

function degreesToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function autoLayoutCircle(count: number): { x: number; y: number }[] {
  return Array.from({ length: count }, (_, i) => {
    const angle = (2 * Math.PI * i) / count;
    return { x: Math.sin(angle), y: Math.cos(angle) };
  });
}

const SpeakingIndicator: React.FC<{ cx: number; cy: number; radius: number }> = ({
  cx, cy, radius,
}) => (
  <>
    <circle
      cx={cx}
      cy={cy}
      r={radius + 6}
      fill="none"
      stroke="#22c55e"
      strokeWidth={2}
      opacity={0.8}
    >
      <animate attributeName="r" from={radius + 4} to={radius + 12} dur="0.8s" repeatCount="indefinite" />
      <animate attributeName="opacity" from={0.8} to={0} dur="0.8s" repeatCount="indefinite" />
    </circle>
  </>
);

const ListenerMarker: React.FC = () => (
  <g>
    <circle cx={CENTER} cy={CENTER} r={18} fill="#6366f1" opacity={0.9} />
    <text x={CENTER} y={CENTER + 5} textAnchor="middle" fill="white" fontSize={12} fontWeight="bold">
      You
    </text>
  </g>
);

const SpatialAudioMap: React.FC<SpatialAudioMapProps> = ({
  participants,
  onPositionChange,
  roomShape = 'circle',
  className = '',
}) => {
  const [positions, setPositions] = useState<{ [id: string]: { x: number; y: number } }>({});
  const [dragging, setDragging] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (participants.length === 0) return;
    const layout = autoLayoutCircle(participants.length);
    const newPositions: { [id: string]: { x: number; y: number } } = {};
    participants.forEach((p, i) => {
      newPositions[p.id] = positions[p.id] || layout[i];
    });
    setPositions(newPositions);
  }, [participants.length]);

  const handleMouseDown = (e: React.MouseEvent, participantId: string) => {
    e.preventDefault();
    setDragging(participantId);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const x = (px - CENTER) / ROOM_RADIUS;
    const y = -(py - CENTER) / ROOM_RADIUS;
    const dist = Math.sqrt(x * x + y * y);
    const clampedX = dist > 1 ? x / dist : x;
    const clampedY = dist > 1 ? y / dist : y;
    setPositions(prev => ({ ...prev, [dragging]: { x: clampedX, y: clampedY } }));
    onPositionChange?.(dragging, clampedX, clampedY);
  };

  const handleMouseUp = () => setDragging(null);

  const getAzimuth = (x: number, y: number): number => {
    return (Math.atan2(x, y) * 180) / Math.PI;
  };

  const getDistance = (x: number, y: number): number => {
    return Math.sqrt(x * x + y * y);
  };

  return (
    <div className={`spatial-audio-map ${className}`} style={{ userSelect: 'none' }}>
      <div style={{ marginBottom: 8, fontWeight: 600, color: '#374151', fontSize: 14 }}>
        🎧 Spatial Audio Map
      </div>

      <svg
        ref={svgRef}
        width={CANVAS_SIZE}
        height={CANVAS_SIZE}
        style={{ background: '#0f172a', borderRadius: 16, cursor: dragging ? 'grabbing' : 'default' }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Room boundary rings */}
        {[0.25, 0.5, 0.75, 1.0].map(r => (
          <circle
            key={r}
            cx={CENTER}
            cy={CENTER}
            r={r * ROOM_RADIUS}
            fill="none"
            stroke="#1e293b"
            strokeWidth={1}
          />
        ))}

        {/* Azimuth lines */}
        {[0, 45, 90, 135].map(deg => {
          const rad = degreesToRad(deg);
          return (
            <line
              key={deg}
              x1={CENTER + Math.sin(rad) * ROOM_RADIUS}
              y1={CENTER - Math.cos(rad) * ROOM_RADIUS}
              x2={CENTER - Math.sin(rad) * ROOM_RADIUS}
              y2={CENTER + Math.cos(rad) * ROOM_RADIUS}
              stroke="#1e293b"
              strokeWidth={1}
            />
          );
        })}

        {/* Direction labels */}
        <text x={CENTER} y={24} textAnchor="middle" fill="#475569" fontSize={11}>Front</text>
        <text x={CENTER} y={CANVAS_SIZE - 8} textAnchor="middle" fill="#475569" fontSize={11}>Behind</text>
        <text x={8} y={CENTER + 4} textAnchor="start" fill="#475569" fontSize={11}>L</text>
        <text x={CANVAS_SIZE - 8} y={CENTER + 4} textAnchor="end" fill="#475569" fontSize={11}>R</text>

        {/* Listener (self) at center */}
        <ListenerMarker />

        {/* Participant nodes */}
        {participants.map(participant => {
          const pos = positions[participant.id] || { x: 0.8, y: 0 };
          const { cx, cy } = posToCanvas(pos.x, pos.y);
          const isHovered = hovered === participant.id;
          const az = getAzimuth(pos.x, pos.y).toFixed(0);
          const dist = getDistance(pos.x, pos.y).toFixed(2);

          return (
            <g
              key={participant.id}
              style={{ cursor: 'grab' }}
              onMouseDown={e => handleMouseDown(e, participant.id)}
              onMouseEnter={() => setHovered(participant.id)}
              onMouseLeave={() => setHovered(null)}
            >
              {participant.isSpeaking && (
                <SpeakingIndicator cx={cx} cy={cy} radius={AVATAR_RADIUS} />
              )}
              <circle
                cx={cx}
                cy={cy}
                r={AVATAR_RADIUS}
                fill={participant.isMuted ? '#475569' : isHovered ? '#818cf8' : '#4f46e5'}
                stroke={participant.isSpeaking ? '#22c55e' : 'none'}
                strokeWidth={2}
              />
              <text
                x={cx}
                y={cy + 4}
                textAnchor="middle"
                fill="white"
                fontSize={9}
                fontWeight="500"
              >
                {participant.displayName.slice(0, 8)}
              </text>
              {participant.isMuted && (
                <text x={cx + 16} y={cy - 16} fontSize={12}>🔇</text>
              )}

              {/* Tooltip on hover */}
              {isHovered && (
                <g>
                  <rect
                    x={cx + 28}
                    y={cy - 30}
                    width={110}
                    height={52}
                    rx={6}
                    fill="#1e293b"
                    stroke="#334155"
                    strokeWidth={1}
                  />
                  <text x={cx + 34} y={cy - 14} fill="#94a3b8" fontSize={10}>
                    Az: {az}°  Dist: {dist}
                  </text>
                  <text x={cx + 34} y={cy} fill="#94a3b8" fontSize={10}>
                    {participant.isMuted ? 'Muted' : participant.isSpeaking ? 'Speaking' : 'Silent'}
                  </text>
                  <text x={cx + 34} y={cy + 14} fill="#64748b" fontSize={9}>
                    Drag to reposition
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div style={{
        marginTop: 12,
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#64748b',
        flexWrap: 'wrap',
      }}>
        <span>
          <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#4f46e5', marginRight: 4 }} />
          Participant
        </span>
        <span>
          <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#22c55e', marginRight: 4 }} />
          Speaking
        </span>
        <span>
          <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#475569', marginRight: 4 }} />
          Muted
        </span>
        <span>
          <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: '#6366f1', marginRight: 4 }} />
          You (listener)
        </span>
      </div>

      {/* Participant list */}
      {participants.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6 }}>
            Participants ({participants.length})
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {participants.map(p => {
              const pos = positions[p.id] || { x: 0, y: 0 };
              return (
                <div
                  key={p.id}
                  style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    padding: '4px 10px',
                    fontSize: 11,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <span style={{ color: p.isSpeaking ? '#22c55e' : '#94a3b8' }}>●</span>
                  <span style={{ fontWeight: 500 }}>{p.displayName}</span>
                  <span style={{ color: '#94a3b8' }}>
                    {getAzimuth(pos.x, pos.y).toFixed(0)}°
                  </span>
                  {p.isMuted && <span title="Muted">🔇</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SpatialAudioMap;
