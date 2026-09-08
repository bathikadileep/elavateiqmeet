import React, { useState } from 'react';
import { Image, Sparkles, Sliders, Eye } from 'lucide-react';

export const VirtualBackgroundCanvas: React.FC = () => {
  const [blurLevel, setBlurLevel] = useState<number>(15);
  const [selectedBg, setSelectedBg] = useState<string>('blur');

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-purple-400" />
          <div>
            <h2 className="text-lg font-bold text-white">AI Virtual Background & Segmentation</h2>
            <p className="text-xs text-slate-400">MediaPipe Selfie Segmentation with WebGL GPU blur acceleration</p>
          </div>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <div className="flex gap-3">
          {['none', 'blur', 'office', 'san_francisco'].map((bg) => (
            <button
              key={bg}
              onClick={() => setSelectedBg(bg)}
              className={`rounded-xl border px-4 py-2.5 text-xs font-semibold capitalize transition-all ${selectedBg === bg ? 'border-purple-500 bg-purple-500/20 text-purple-300' : 'border-slate-800 bg-slate-950 text-slate-400'}`}
            >
              {bg.replace('_', ' ')}
            </button>
          ))}
        </div>

        {selectedBg === 'blur' && (
          <div className="mt-4">
            <label className="block text-xs font-semibold text-slate-300">Bokeh Blur Radius ({blurLevel}px)</label>
            <input
              type="range"
              min="0"
              max="30"
              value={blurLevel}
              onChange={(e) => setBlurLevel(Number(e.target.value))}
              className="mt-2 w-full accent-purple-500"
            />
          </div>
        )}
      </div>
    </div>
  );
};
