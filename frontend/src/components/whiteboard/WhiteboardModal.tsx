import React from 'react';
import { X, Edit3, Eraser, Square, Circle, MoveRight, StickyNote, RotateCcw, Trash2, Download } from 'lucide-react';
import Canvas from './Canvas';
import type { WhiteboardTool, WhiteboardStroke } from '../../types/collaboration';

export interface WhiteboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  strokes: WhiteboardStroke[];
  activeTool: WhiteboardTool;
  activeColor: string;
  strokeWidth: number;
  canUndo: boolean;
  onSelectTool: (tool: WhiteboardTool) => void;
  onSelectColor: (color: string) => void;
  onSelectWidth: (width: number) => void;
  onAddStroke: (stroke: WhiteboardStroke) => void;
  onClear: () => void;
  onUndo: () => void;
}

export const WhiteboardModal: React.FC<WhiteboardModalProps> = ({
  isOpen,
  onClose,
  strokes,
  activeTool,
  activeColor,
  strokeWidth,
  canUndo,
  onSelectTool,
  onSelectColor,
  onSelectWidth,
  onAddStroke,
  onClear,
  onUndo,
}) => {
  if (!isOpen) return null;

  const colors = ['#ffffff', '#6366f1', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  const exportAsPNG = () => {
    const canvas = document.querySelector('canvas');
    if (canvas) {
      const image = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `elevateiq-whiteboard-${Date.now()}.png`;
      link.href = image;
      link.click();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-6xl h-[90vh] rounded-3xl glass-card border border-white/10 bg-[#080911]/95 p-6 text-white shadow-2xl flex flex-col justify-between overflow-hidden">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Edit3 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Interactive Canvas Whiteboard</h2>
              <p className="text-xs text-gray-400">Multi-user real-time vector whiteboard</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={exportAsPNG}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors flex items-center gap-2 shadow-lg shadow-indigo-600/30 cursor-pointer"
            >
              <Download className="w-4 h-4" /> Export PNG
            </button>

            <button
              onClick={onClose}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar & Canvas Container */}
        <div className="flex-1 flex gap-4 py-4 overflow-hidden">
          {/* Vertical Toolbar */}
          <div className="w-16 p-2 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center gap-3 justify-between">
            <div className="flex flex-col gap-2">
              <button
                onClick={() => onSelectTool('pencil')}
                title="Pencil"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'pencil' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <Edit3 className="w-5 h-5" />
              </button>

              <button
                onClick={() => onSelectTool('eraser')}
                title="Eraser"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'eraser' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <Eraser className="w-5 h-5" />
              </button>

              <button
                onClick={() => onSelectTool('rectangle')}
                title="Rectangle"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'rectangle' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <Square className="w-5 h-5" />
              </button>

              <button
                onClick={() => onSelectTool('circle')}
                title="Circle"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'circle' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <Circle className="w-5 h-5" />
              </button>

              <button
                onClick={() => onSelectTool('arrow')}
                title="Arrow"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'arrow' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <MoveRight className="w-5 h-5" />
              </button>

              <button
                onClick={() => onSelectTool('sticky')}
                title="Sticky Note"
                className={`p-3 rounded-xl transition-all cursor-pointer ${
                  activeTool === 'sticky' ? 'bg-amber-500 text-white shadow-lg' : 'text-gray-400 hover:bg-white/10'
                }`}
              >
                <StickyNote className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-col gap-2 border-t border-white/10 pt-2">
              <button
                onClick={onUndo}
                disabled={!canUndo}
                title="Undo"
                className={`p-3 rounded-xl transition-all ${
                  canUndo ? 'text-gray-300 hover:bg-white/10 cursor-pointer' : 'text-gray-600 opacity-50 cursor-not-allowed'
                }`}
              >
                <RotateCcw className="w-5 h-5" />
              </button>

              <button
                onClick={onClear}
                title="Clear Canvas"
                className="p-3 rounded-xl text-rose-400 hover:bg-rose-500/20 transition-all cursor-pointer"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Canvas Component */}
          <div className="flex-1 h-full relative">
            <Canvas
              strokes={strokes}
              activeTool={activeTool}
              activeColor={activeColor}
              strokeWidth={strokeWidth}
              onAddStroke={onAddStroke}
            />
          </div>
        </div>

        {/* Footer Palette Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-white/10 text-xs">
          <div className="flex items-center gap-3">
            <span className="text-gray-400 font-medium">Color:</span>
            <div className="flex items-center gap-1.5">
              {colors.map((c) => (
                <button
                  key={c}
                  onClick={() => onSelectColor(c)}
                  style={{ backgroundColor: c }}
                  className={`w-6 h-6 rounded-full border border-white/20 transition-transform cursor-pointer ${
                    activeColor === c ? 'scale-125 ring-2 ring-indigo-400' : 'hover:scale-110'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-gray-400 font-medium">Width:</span>
            <input
              type="range"
              min="1"
              max="15"
              value={strokeWidth}
              onChange={(e) => onSelectWidth(Number(e.target.value))}
              className="accent-indigo-500 cursor-pointer"
            />
            <span className="text-gray-300 font-bold w-4 text-center">{strokeWidth}px</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhiteboardModal;
