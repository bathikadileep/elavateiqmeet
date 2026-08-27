import React, { useRef, useEffect, useState } from 'react';
import type { WhiteboardTool, WhiteboardStroke } from '../../types/collaboration';

export interface CanvasProps {
  strokes: WhiteboardStroke[];
  activeTool: WhiteboardTool;
  activeColor: string;
  strokeWidth: number;
  onAddStroke: (stroke: WhiteboardStroke) => void;
}

export const Canvas: React.FC<CanvasProps> = ({
  strokes,
  activeTool,
  activeColor,
  strokeWidth,
  onAddStroke,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPoints, setCurrentPoints] = useState<number[]>([]);

  // Render all vector strokes onto HTML5 Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    strokes.forEach((stroke) => {
      ctx.save();
      ctx.strokeStyle = stroke.tool === 'eraser' ? '#0c0e1a' : stroke.color;
      ctx.fillStyle = stroke.color;
      ctx.lineWidth = stroke.width;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      const pts = stroke.points;
      if (pts.length < 4) {
        ctx.restore();
        return;
      }

      if (stroke.tool === 'pencil' || stroke.tool === 'eraser') {
        ctx.beginPath();
        ctx.moveTo(pts[0], pts[1]);
        for (let i = 2; i < pts.length; i += 2) {
          ctx.lineTo(pts[i], pts[i + 1]);
        }
        ctx.stroke();
      } else if (stroke.tool === 'rectangle') {
        const width = pts[pts.length - 2] - pts[0];
        const height = pts[pts.length - 1] - pts[1];
        ctx.strokeRect(pts[0], pts[1], width, height);
      } else if (stroke.tool === 'circle') {
        const rx = (pts[pts.length - 2] - pts[0]) / 2;
        const ry = (pts[pts.length - 1] - pts[1]) / 2;
        const cx = pts[0] + rx;
        const cy = pts[1] + ry;
        ctx.beginPath();
        ctx.ellipse(cx, cy, Math.abs(rx), Math.abs(ry), 0, 0, 2 * Math.PI);
        ctx.stroke();
      } else if (stroke.tool === 'arrow') {
        const x1 = pts[0];
        const y1 = pts[1];
        const x2 = pts[pts.length - 2];
        const y2 = pts[pts.length - 1];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();

        // Arrow head
        const angle = Math.atan2(y2 - y1, x2 - x1);
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - 12 * Math.cos(angle - Math.PI / 6), y2 - 12 * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(x2 - 12 * Math.cos(angle + Math.PI / 6), y2 - 12 * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
      } else if (stroke.tool === 'sticky') {
        ctx.fillStyle = stroke.color || '#fef08a';
        ctx.fillRect(pts[0], pts[1], 140, 120);
        ctx.fillStyle = '#1e293b';
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.fillText(stroke.text || 'Idea Note', pts[0] + 12, pts[1] + 30);
      }

      ctx.restore();
    });
  }, [strokes]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsDrawing(true);
    setCurrentPoints([x, y]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setCurrentPoints((prev) => [...prev, x, y]);
  };

  const handleMouseUp = () => {
    if (!isDrawing || currentPoints.length < 2) {
      setIsDrawing(false);
      return;
    }

    const stroke: WhiteboardStroke = {
      id: Math.random().toString(36).substring(2, 9),
      tool: activeTool,
      points: currentPoints,
      color: activeColor,
      width: strokeWidth,
      text: activeTool === 'sticky' ? 'Note Idea' : undefined,
    };

    onAddStroke(stroke);
    setIsDrawing(false);
    setCurrentPoints([]);
  };

  return (
    <canvas
      ref={canvasRef}
      width={1200}
      height={700}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      className="w-full h-full bg-[#0c0e1a] border border-white/10 rounded-2xl cursor-crosshair shadow-inner"
    />
  );
};

export default Canvas;
