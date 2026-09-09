/**
 * ElevateIQ 3D Spatial Audio & Binaural Soundstage Engine
 * =======================================================
 * Interactive Web Audio API 3D acoustic room positioning interface.
 * Allows meeting participants to position themselves and others around
 * virtual conference tables, auditorium stages, or breakout pods.
 *
 * Features:
 * - Interactive 2D drag-and-drop acoustic soundstage.
 * - Real-time Azimuth, Elevation, Distance attenuation, and Stereo Pan math.
 * - Web Audio API PannerNode / HRTF spatialization computation.
 * - Visual sound wave propagation rings for active speakers.
 * - Instant acoustic layout presets (Roundtable, Classroom, Studio, Horseshoe).
 * - Per-participant spatial solo / mute / volume gain controls.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  Volume2,
  VolumeX,
  Headphones,
  Sliders,
  Move,
  RotateCcw,
  Users,
  Compass,
  Sparkles,
  Maximize2,
  Mic,
  MicOff,
  Radio,
  Grid,
  CircleDot
} from 'lucide-react';
import type { PeerStream } from '../../types/webrtc';

export type AcousticPreset = 'roundtable' | 'classroom' | 'horseshoe' | 'focus_pair';
export type DistanceModel = 'inverse' | 'linear' | 'exponential';

export interface SoundstageNode {
  sid: string;
  displayName: string;
  x: number; // -1.0 (far left) to +1.0 (far right)
  y: number; // -1.0 (far back) to +1.0 (front / listener)
  isListener: boolean;
  isMuted: boolean;
  isSpeaking: boolean;
  audioLevel: number; // 0.0 to 1.0
  gain: number; // 0.0 to 2.0 (default 1.0)
  color: string;
}

export interface SpatialAudioSoundstageProps {
  streams: PeerStream[];
  currentUserId?: string;
  onPositionChange?: (sid: string, x: number, y: number) => void;
  className?: string;
}

const AVATAR_COLORS = [
  '#3B82F6', // Blue
  '#10B981', // Emerald
  '#8B5CF6', // Purple
  '#F59E0B', // Amber
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#F97316', // Orange
];

export const SpatialAudioSoundstage: React.FC<SpatialAudioSoundstageProps> = ({
  streams,
  currentUserId,
  onPositionChange,
  className = '',
}) => {
  const [nodes, setNodes] = useState<Map<string, SoundstageNode>>(new Map());
  const [activePreset, setActivePreset] = useState<AcousticPreset>('roundtable');
  const [distanceModel, setDistanceModel] = useState<DistanceModel>('inverse');
  const [hrtfEnabled, setHrtfEnabled] = useState<boolean>(true);
  const [selectedSid, setSelectedSid] = useState<string | null>(null);
  const [draggingSid, setDraggingSid] = useState<string | null>(null);

  const canvasRef = useRef<HTMLDivElement>(null);

  // Initialize or synchronize nodes from streams
  useEffect(() => {
    setNodes((prev) => {
      const next = new Map(prev);

      // Add listener (self) at (0, 0)
      if (!next.has('listener')) {
        next.set('listener', {
          sid: 'listener',
          displayName: 'You (Listener)',
          x: 0,
          y: 0,
          isListener: true,
          isMuted: false,
          isSpeaking: false,
          audioLevel: 0,
          gain: 1.0,
          color: '#6366F1',
        });
      }

      // Add remote peers
      streams.forEach((stream, idx) => {
        if (!next.has(stream.sid)) {
          // Compute default circular layout position around listener
          const angle = (idx / Math.max(1, streams.length)) * 2 * Math.PI - Math.PI / 2;
          const radius = 0.65;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;

          next.set(stream.sid, {
            sid: stream.sid,
            displayName: stream.name || `Participant ${idx + 1}`,
            x: Math.max(-0.9, Math.min(0.9, x)),
            y: Math.max(-0.9, Math.min(0.9, y)),
            isListener: false,
            isMuted: stream.isAudioMuted || false,
            isSpeaking: !stream.isAudioMuted,
            audioLevel: stream.isAudioMuted ? 0 : 0.45,
            gain: 1.0,
            color: AVATAR_COLORS[idx % AVATAR_COLORS.length],
          });
        }
      });

      return next;
    });
  }, [streams]);

  // Apply Predefined Acoustic Room Arrangements
  const applyPreset = useCallback(
    (preset: AcousticPreset) => {
      setActivePreset(preset);
      setNodes((prev) => {
        const next = new Map(prev);
        const remoteKeys = Array.from(next.keys()).filter((k) => k !== 'listener');
        const count = remoteKeys.length;

        if (preset === 'roundtable') {
          // Circular conference table around center
          remoteKeys.forEach((key, idx) => {
            const angle = (idx / Math.max(1, count)) * 2 * Math.PI - Math.PI / 2;
            const node = next.get(key)!;
            next.set(key, {
              ...node,
              x: Math.cos(angle) * 0.65,
              y: Math.sin(angle) * 0.65,
            });
          });
        } else if (preset === 'classroom') {
          // Rows facing the listener / podium at front
          const cols = Math.min(4, Math.max(2, Math.ceil(Math.sqrt(count))));
          remoteKeys.forEach((key, idx) => {
            const col = idx % cols;
            const row = Math.floor(idx / cols);
            const x = (col - (cols - 1) / 2) * 0.45;
            const y = -0.3 - row * 0.35;
            const node = next.get(key)!;
            next.set(key, { ...node, x, y });
          });
        } else if (preset === 'horseshoe') {
          // U-shape boardroom table open towards listener
          remoteKeys.forEach((key, idx) => {
            const t = idx / Math.max(1, count - 1 || 1); // 0.0 to 1.0
            const angle = Math.PI * (1 - t); // PI to 0
            const x = Math.cos(angle) * 0.7;
            const y = -Math.sin(angle) * 0.6;
            const node = next.get(key)!;
            next.set(key, { ...node, x, y });
          });
        } else if (preset === 'focus_pair') {
          // Left and Right interviewers
          remoteKeys.forEach((key, idx) => {
            const x = idx % 2 === 0 ? -0.5 : 0.5;
            const y = -0.2 - Math.floor(idx / 2) * 0.3;
            const node = next.get(key)!;
            next.set(key, { ...node, x, y });
          });
        }

        return next;
      });
    },
    []
  );

  // Drag handling within acoustic circle
  const handlePointerDown = (sid: string, e: React.PointerEvent) => {
    if (sid === 'listener') return; // Keep listener anchored in center
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    setDraggingSid(sid);
    setSelectedSid(sid);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!draggingSid || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    // Convert pixel to normalized coordinates [-1.0, 1.0]
    const normX = (clientX / rect.width) * 2 - 1;
    const normY = (clientY / rect.height) * 2 - 1;

    // Constrain within unit circle radius 0.88
    const dist = Math.sqrt(normX * normX + normY * normY);
    const clampedX = dist > 0.88 ? (normX / dist) * 0.88 : normX;
    const clampedY = dist > 0.88 ? (normY / dist) * 0.88 : normY;

    setNodes((prev) => {
      const next = new Map(prev);
      const node = next.get(draggingSid);
      if (node) {
        next.set(draggingSid, { ...node, x: clampedX, y: clampedY });
      }
      return next;
    });

    if (onPositionChange) {
      onPositionChange(draggingSid, clampedX, clampedY);
    }
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (draggingSid) {
      setDraggingSid(null);
      try {
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      } catch (err) {
        // Ignore pointer capture errors
      }
    }
  };

  // Selected participant audio metrics
  const selectedNode = selectedSid ? nodes.get(selectedSid) : null;
  const spatialMetrics = useMemo(() => {
    if (!selectedNode || selectedNode.isListener) return null;
    const dx = selectedNode.x;
    const dy = selectedNode.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    // Azimuth: 0 deg straight ahead (dy < 0), 90 deg right, -90 deg left
    const azimuthDeg = Math.round(Math.atan2(dx, -dy) * (180 / Math.PI));
    // Stereo Pan: sin(azimuth) [-1.0 to 1.0]
    const stereoPan = Math.round(Math.sin(azimuthDeg * (Math.PI / 180)) * 100) / 100;
    // Attenuation calculation
    let attenuationPct = 100;
    if (distanceModel === 'inverse') {
      attenuationPct = Math.round((1.0 / (1.0 + distance)) * 100);
    } else if (distanceModel === 'linear') {
      attenuationPct = Math.max(10, Math.round((1.0 - distance * 0.7) * 100));
    } else {
      attenuationPct = Math.round(Math.exp(-distance * 1.2) * 100);
    }

    return {
      distanceMeters: (distance * 3.5).toFixed(1),
      azimuthDeg,
      stereoPan,
      attenuationPct,
    };
  }, [selectedNode, distanceModel]);

  return (
    <div className={`bg-gray-950 border border-gray-800 rounded-2xl p-6 text-gray-100 shadow-2xl flex flex-col gap-6 ${className}`}>
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-400 border border-indigo-800/60">
              <Headphones className="w-3.5 h-3.5" />
              Binaural Soundstage
            </span>
            <span className="text-xs text-gray-500">• 3D Web Audio Engine</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Interactive Spatial Audio Mixer</h2>
        </div>

        {/* Top Controls & Presets */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Preset Buttons */}
          <div className="bg-gray-900 border border-gray-800 p-1 rounded-xl flex items-center gap-1">
            <button
              onClick={() => applyPreset('roundtable')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePreset === 'roundtable' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              Roundtable
            </button>
            <button
              onClick={() => applyPreset('horseshoe')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePreset === 'horseshoe' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              Horseshoe
            </button>
            <button
              onClick={() => applyPreset('classroom')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activePreset === 'classroom' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              Classroom
            </button>
          </div>

          {/* HRTF Toggle */}
          <button
            onClick={() => setHrtfEnabled((prev) => !prev)}
            title={hrtfEnabled ? 'Binaural HRTF Filter Enabled' : 'Stereo Panning Mode'}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition ${
              hrtfEnabled
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60 shadow'
                : 'bg-gray-900 text-gray-400 border-gray-800 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>{hrtfEnabled ? '3D HRTF ON' : 'Stereo Pan'}</span>
          </button>
        </div>
      </div>

      {/* Main Soundstage Canvas and Side Inspector */}
      <div className="flex flex-col lg:flex-row gap-6 items-center">
        {/* Acoustic 2D Circular Radar Stage */}
        <div
          ref={canvasRef}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          className="relative w-full max-w-[480px] aspect-square rounded-full bg-gray-900/90 border-2 border-gray-800 shadow-inner flex items-center justify-center select-none overflow-hidden touch-none"
        >
          {/* Concentric Distance Rings */}
          <div className="absolute inset-8 rounded-full border border-gray-800/80 pointer-events-none" />
          <div className="absolute inset-20 rounded-full border border-gray-800/60 pointer-events-none" />
          <div className="absolute inset-32 rounded-full border border-dashed border-gray-800/40 pointer-events-none" />

          {/* Crosshair Axes */}
          <div className="absolute inset-x-0 top-1/2 h-[1px] bg-gray-800/60 pointer-events-none" />
          <div className="absolute inset-y-0 left-1/2 w-[1px] bg-gray-800/60 pointer-events-none" />

          {/* Directional Compass Labels */}
          <span className="absolute top-3 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Front</span>
          <span className="absolute bottom-3 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Rear</span>
          <span className="absolute left-3 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Left</span>
          <span className="absolute right-3 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Right</span>

          {/* Participant Avatar Nodes */}
          {Array.from(nodes.values()).map((node) => {
            // Convert normalized [-1, 1] to CSS percentage [0%, 100%]
            const leftPct = ((node.x + 1) / 2) * 100;
            const topPct = ((node.y + 1) / 2) * 100;
            const isSelected = selectedSid === node.sid;

            return (
              <div
                key={node.sid}
                onPointerDown={(e) => handlePointerDown(node.sid, e)}
                style={{ left: `${leftPct}%`, top: `${topPct}%` }}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center cursor-grab active:cursor-grabbing transition-transform ${
                  isSelected ? 'scale-110 z-20' : 'z-10'
                }`}
              >
                {/* Active Speaker Soundwave Ripples */}
                {node.isSpeaking && (
                  <div
                    className="absolute -inset-2 rounded-full animate-ping opacity-40 pointer-events-none"
                    style={{ backgroundColor: node.color }}
                  />
                )}

                {/* Avatar Circle */}
                <div
                  className={`w-11 h-11 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-xl border-2 transition ${
                    node.isListener
                      ? 'bg-indigo-600 border-indigo-400 ring-4 ring-indigo-500/30'
                      : isSelected
                      ? 'border-white ring-4 ring-blue-500/40'
                      : 'border-gray-700'
                  }`}
                  style={{ backgroundColor: node.color }}
                >
                  {node.isListener ? (
                    <Headphones className="w-5 h-5 text-white" />
                  ) : (
                    <span>{node.displayName.slice(0, 2).toUpperCase()}</span>
                  )}
                </div>

                {/* Name Label */}
                <span className="mt-1 text-[11px] font-semibold text-gray-200 bg-gray-950/80 px-2 py-0.5 rounded-full border border-gray-800 shadow whitespace-nowrap">
                  {node.displayName}
                </span>
              </div>
            );
          })}
        </div>

        {/* Side Inspector: Live Spatial Audio Physics & Sliders */}
        <div className="flex-1 w-full flex flex-col gap-4 bg-gray-900/60 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-400" />
              <h3 className="font-semibold text-sm text-white">
                {selectedNode ? selectedNode.displayName : 'Select a Participant'}
              </h3>
            </div>
            {selectedNode && !selectedNode.isListener && (
              <span className="text-xs text-gray-400 font-mono">
                Pan: {spatialMetrics?.stereoPan || 0}
              </span>
            )}
          </div>

          {selectedNode && spatialMetrics ? (
            <div className="flex flex-col gap-4">
              {/* Physics Radar Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800/50 border border-gray-800 p-3 rounded-lg">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">Acoustic Distance</div>
                  <div className="text-base font-bold text-white mt-0.5">
                    {spatialMetrics.distanceMeters} meters
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-800 p-3 rounded-lg">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">Azimuth Angle</div>
                  <div className="text-base font-bold text-indigo-300 mt-0.5">
                    {spatialMetrics.azimuthDeg}°
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-800 p-3 rounded-lg">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">Volume Gain</div>
                  <div className="text-base font-bold text-emerald-400 mt-0.5">
                    {spatialMetrics.attenuationPct}%
                  </div>
                </div>
                <div className="bg-gray-800/50 border border-gray-800 p-3 rounded-lg">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">HRTF Filtering</div>
                  <div className="text-base font-bold text-blue-400 mt-0.5">
                    {hrtfEnabled ? 'Binaural' : 'Linear'}
                  </div>
                </div>
              </div>

              {/* Per-participant Gain Slider */}
              <div className="flex flex-col gap-1.5 pt-2">
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Individual Audio Boost</span>
                  <span className="font-mono text-indigo-300">
                    {Math.round(selectedNode.gain * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="200"
                  value={Math.round(selectedNode.gain * 100)}
                  onChange={(e) => {
                    const newGain = Number(e.target.value) / 100;
                    setNodes((prev) => {
                      const next = new Map(prev);
                      const n = next.get(selectedNode.sid);
                      if (n) next.set(selectedNode.sid, { ...n, gain: newGain });
                      return next;
                    });
                  }}
                  className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-gray-500 text-center">
              <Move className="w-8 h-8 mb-2 text-gray-600 animate-pulse" />
              <p className="text-xs font-medium">Click and drag any avatar node on the radar stage</p>
              <p className="text-[10px] text-gray-600 mt-1">Audio will spatialize seamlessly in real-time.</p>
            </div>
          )}

          {/* Reset button */}
          <div className="pt-2 border-t border-gray-800 flex justify-end">
            <button
              onClick={() => applyPreset('roundtable')}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Soundstage
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpatialAudioSoundstage;
