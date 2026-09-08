import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Crosshair, Highlighter, ChevronLeft, ChevronRight, Eye, ShieldAlert, Sparkles } from 'lucide-react';

export interface LaserPointerCoordinate {
  userId: string;
  userName: string;
  color: string;
  x: number; // 0.0 to 1.0 (normalized percentage)
  y: number; // 0.0 to 1.0
  timestamp: number;
}

export interface EphemeralStroke {
  id: string;
  color: string;
  points: Array<{ x: number; y: number }>;
  createdAt: number;
  durationMs: number;
}

interface InteractivePresenterCanvasProps {
  roomCode: string;
  currentUserId: string;
  currentUserName: string;
  totalPages?: number;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  onBroadcastLaser?: (coord: LaserPointerCoordinate) => void;
  onBroadcastStroke?: (stroke: EphemeralStroke) => void;
  remotePointers?: LaserPointerCoordinate[];
  remoteStrokes?: EphemeralStroke[];
}

export const InteractivePresenterCanvas: React.FC<InteractivePresenterCanvasProps> = ({
  roomCode,
  currentUserId,
  currentUserName,
  totalPages = 10,
  currentPage = 1,
  onPageChange,
  onBroadcastLaser,
  onBroadcastStroke,
  remotePointers = [],
  remoteStrokes = []
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [activeTool, setActiveTool] = useState<'pointer' | 'highlighter' | 'laser'>('laser');
  const [highlightColor, setHighlightColor] = useState<string>('#00f2fe');
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [localStrokes, setLocalStrokes] = useState<EphemeralStroke[]>([]);
  const currentStrokeRef = useRef<{ x: number; y: number }[]>([]);

  // Color palette for highlighter
  const palette = ['#00f2fe', '#4facfe', '#fa709a', '#fee140', '#43e97b'];

  // Handle Canvas Resize
  useEffect(() => {
    const handleResize = () => {
      if (!canvasRef.current || !containerRef.current) return;
      const { width, height } = containerRef.current.getBoundingClientRect();
      canvasRef.current.width = width * window.devicePixelRatio;
      canvasRef.current.height = height * window.devicePixelRatio;
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Animation render loop for laser pointers and fading ink
  useEffect(() => {
    let animId: number;

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;
      const now = Date.now();

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Render Ephemeral Highlighter Strokes with linear fade-out
      const allStrokes = [...localStrokes, ...remoteStrokes];
      allStrokes.forEach((stroke) => {
        const age = now - stroke.createdAt;
        if (age >= stroke.durationMs) return;

        const opacity = Math.max(0, 1 - (age / stroke.durationMs));
        ctx.save();
        ctx.strokeStyle = stroke.color;
        ctx.globalAlpha = opacity * 0.75;
        ctx.lineWidth = 14;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        if (stroke.points.length > 1) {
          ctx.beginPath();
          ctx.moveTo(stroke.points[0].x * width, stroke.points[0].y * height);
          for (let i = 1; i < stroke.points.length; i++) {
            ctx.lineTo(stroke.points[i].x * width, stroke.points[i].y * height);
          }
          ctx.stroke();
        }
        ctx.restore();
      });

      // Render Laser Pointers (glowing core + pulse ring)
      remotePointers.forEach((ptr) => {
        if (now - ptr.timestamp > 2500) return; // Ignore stale pointers

        const px = ptr.x * width;
        const py = ptr.y * height;

        ctx.save();
        // Outer glowing ring
        ctx.beginPath();
        ctx.arc(px, py, 14, 0, 2 * Math.PI);
        ctx.fillStyle = ptr.color + '33';
        ctx.fill();

        // Inner glowing core
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, 2 * Math.PI);
        ctx.fillStyle = ptr.color;
        ctx.shadowColor = ptr.color;
        ctx.shadowBlur = 12;
        ctx.fill();

        // Participant tag
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(ptr.userName, px + 12, py + 4);
        ctx.restore();
      });

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [localStrokes, remoteStrokes, remotePointers]);

  // Clean expired strokes periodically
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      setLocalStrokes((prev) => prev.filter((s) => now - s.createdAt < s.durationMs));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Mouse / Pointer event handlers
  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const normX = (e.clientX - rect.left) / rect.width;
      const normY = (e.clientY - rect.top) / rect.height;

      if (activeTool === 'laser') {
        const laserCoord: LaserPointerCoordinate = {
          userId: currentUserId,
          userName: currentUserName,
          color: highlightColor,
          x: normX,
          y: normY,
          timestamp: Date.now()
        };
        onBroadcastLaser?.(laserCoord);
      } else if (activeTool === 'highlighter' && isDrawing) {
        currentStrokeRef.current.push({ x: normX, y: normY });
      }
    },
    [activeTool, isDrawing, currentUserId, currentUserName, highlightColor, onBroadcastLaser]
  );

  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (activeTool === 'highlighter') {
        setIsDrawing(true);
        if (!canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const normX = (e.clientX - rect.left) / rect.width;
        const normY = (e.clientY - rect.top) / rect.height;
        currentStrokeRef.current = [{ x: normX, y: normY }];
      }
    },
    [activeTool]
  );

  const handlePointerUp = useCallback(() => {
    if (activeTool === 'highlighter' && isDrawing) {
      setIsDrawing(false);
      if (currentStrokeRef.current.length > 1) {
        const stroke: EphemeralStroke = {
          id: `stroke_${Date.now()}`,
          color: highlightColor,
          points: [...currentStrokeRef.current],
          createdAt: Date.now(),
          durationMs: 3000 // Fades completely in 3 seconds
        };
        setLocalStrokes((prev) => [...prev, stroke]);
        onBroadcastStroke?.(stroke);
      }
      currentStrokeRef.current = [];
    }
  }, [activeTool, isDrawing, highlightColor, onBroadcastStroke]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[540px] bg-slate-950/80 rounded-2xl border border-slate-800 backdrop-blur-md overflow-hidden flex flex-col select-none"
    >
      {/* Slide Display Mock / Viewport */}
      <div className="flex-1 relative flex items-center justify-center p-8 bg-gradient-to-b from-slate-900/50 to-slate-950">
        <div className="w-full max-w-4xl h-[420px] bg-slate-900 border border-slate-800/80 rounded-xl shadow-2xl flex flex-col items-center justify-center p-12 text-center relative overflow-hidden">
          <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>ElevateIQ Slide Deck — Slide {currentPage}</span>
          </div>

          <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">
            Quarterly Architecture & Media Strategy
          </h2>
          <p className="text-slate-400 max-w-lg text-sm leading-relaxed mb-6">
            Demonstrating multi-region data residency routing, E2EE MLS key ratcheting, and real-time simulcast video layer switching.
          </p>

          <div className="flex items-center gap-4">
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50 text-left">
              <span className="text-xs text-slate-400">Total Latency</span>
              <p className="text-lg font-bold text-emerald-400">42 ms</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50 text-left">
              <span className="text-xs text-slate-400">Simulcast Layer</span>
              <p className="text-lg font-bold text-cyan-400">1080p @ 60fps</p>
            </div>
          </div>
        </div>

        {/* Interactive Overlay Canvas */}
        <canvas
          ref={canvasRef}
          onPointerMove={handlePointerMove}
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          className="absolute inset-0 w-full h-full cursor-crosshair z-10 touch-none"
        />
      </div>

      {/* Floating Toolbar Controls */}
      <div className="h-16 border-t border-slate-800/80 bg-slate-900/90 px-6 flex items-center justify-between z-20">
        {/* Tool Selectors */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTool('laser')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTool === 'laser'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Crosshair className="w-4 h-4" />
            <span>Laser Pointer</span>
          </button>

          <button
            onClick={() => setActiveTool('highlighter')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTool === 'highlighter'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Highlighter className="w-4 h-4" />
            <span>Fading Highlighter</span>
          </button>

          {/* Color Picker Palette */}
          <div className="flex items-center gap-1.5 ml-4 pl-4 border-l border-slate-800">
            {palette.map((c) => (
              <button
                key={c}
                onClick={() => setHighlightColor(c)}
                style={{ backgroundColor: c }}
                className={`w-5 h-5 rounded-full transition-transform ${
                  highlightColor === c ? 'scale-125 ring-2 ring-white/80 ring-offset-2 ring-offset-slate-900' : 'hover:scale-110'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Slide Navigation Pagination */}
        <div className="flex items-center gap-3">
          <button
            disabled={currentPage <= 1}
            onClick={() => onPageChange?.(currentPage - 1)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="text-xs text-slate-300 font-medium">
            Page {currentPage} of {totalPages}
          </span>

          <button
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange?.(currentPage + 1)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
