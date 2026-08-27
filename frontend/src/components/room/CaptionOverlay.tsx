import React from 'react';
import type { SpeechTranscriptItem } from '../../types/ai';

export interface CaptionOverlayProps {
  activeSubtitle: SpeechTranscriptItem | null;
  isEnabled: boolean;
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({ activeSubtitle, isEnabled }) => {
  if (!isEnabled || !activeSubtitle || !activeSubtitle.text.trim()) return null;

  return (
    <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-30 max-w-2xl px-6 py-3 rounded-2xl bg-black/75 backdrop-blur-xl border border-white/10 text-white shadow-2xl animate-fade-in text-center pointer-events-none">
      <span className="text-xs font-semibold text-indigo-400 block mb-0.5 uppercase tracking-wider">
        {activeSubtitle.speaker_name}
      </span>
      <p className="text-base font-medium leading-relaxed tracking-wide text-gray-100">
        "{activeSubtitle.text}"
      </p>
    </div>
  );
};

export default CaptionOverlay;
