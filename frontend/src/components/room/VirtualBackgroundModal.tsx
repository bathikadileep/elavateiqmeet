import React from 'react';
import { X, Sparkles, Sliders, Image, Check } from 'lucide-react';
import type { VirtualBackgroundMode } from '../../types/ai';

export interface VirtualBackgroundModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentMode: VirtualBackgroundMode;
  onSelectMode: (mode: VirtualBackgroundMode) => void;
}

export const VirtualBackgroundModal: React.FC<VirtualBackgroundModalProps> = ({
  isOpen,
  onClose,
  currentMode,
  onSelectMode,
}) => {
  if (!isOpen) return null;

  const options: { mode: VirtualBackgroundMode; title: string; desc: string; icon: any }[] = [
    { mode: 'none', title: 'No Background Effect', desc: 'Default raw camera feed', icon: Sliders },
    { mode: 'blur-low', title: 'Slight Background Blur', desc: 'Subtle focus effect (8px)', icon: Sparkles },
    { mode: 'blur-high', title: 'Deep Background Blur', desc: 'High privacy focus (20px)', icon: Sparkles },
    { mode: 'office', title: 'Executive Studio', desc: 'Modern virtual office preset', icon: Image },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg rounded-3xl glass-card border border-white/10 bg-[#0c0e1a]/95 p-6 text-white shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-purple-500/20 border border-purple-500/30 text-purple-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Virtual Studio & Blur</h2>
              <p className="text-xs text-gray-400">WebGL real-time video background segmentation</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Options Grid */}
        <div className="space-y-3 mb-6">
          {options.map((opt) => {
            const Icon = opt.icon;
            const isSelected = currentMode === opt.mode;

            return (
              <div
                key={opt.mode}
                onClick={() => onSelectMode(opt.mode)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                  isSelected
                    ? 'bg-purple-600/30 border-purple-500 ring-2 ring-purple-500/30'
                    : 'bg-white/5 border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${isSelected ? 'bg-purple-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">{opt.title}</h4>
                    <p className="text-xs text-gray-400">{opt.desc}</p>
                  </div>
                </div>

                {isSelected && <Check className="w-5 h-5 text-purple-400" />}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end pt-3 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs cursor-pointer shadow-lg shadow-purple-600/30"
          >
            Apply & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default VirtualBackgroundModal;
