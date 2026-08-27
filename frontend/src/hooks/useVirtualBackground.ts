import { useState, useCallback } from 'react';
import type { VirtualBackgroundMode } from '../types/ai';

export const useVirtualBackground = () => {
  const [backgroundMode, setBackgroundMode] = useState<VirtualBackgroundMode>('none');
  const [customImageUrl, setCustomImageUrl] = useState<string | null>(null);

  const applyVirtualBackground = useCallback(
    (sourceStream: MediaStream, mode: VirtualBackgroundMode, imageSrc?: string): MediaStream => {
      setBackgroundMode(mode);
      if (imageSrc) setCustomImageUrl(imageSrc);

      if (mode === 'none' || !sourceStream) {
        return sourceStream;
      }

      const videoTrack = sourceStream.getVideoTracks()[0];
      if (!videoTrack) return sourceStream;

      const video = document.createElement('video');
      video.srcObject = sourceStream;
      video.muted = true;
      video.play().catch(() => {});

      const canvas = document.createElement('canvas');
      canvas.width = 1280;
      canvas.height = 720;
      const ctx = canvas.getContext('2d');
      if (!ctx) return sourceStream;

      let animationFrameId: number;

      const renderFrame = () => {
        if (video.readyState >= 2) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          if (mode === 'blur-low' || mode === 'blur-high') {
            ctx.filter = mode === 'blur-low' ? 'blur(8px)' : 'blur(20px)';
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            ctx.filter = 'none';

            // Draw center subject overlay
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          } else {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          }
        }
        animationFrameId = requestAnimationFrame(renderFrame);
      };

      renderFrame();

      const processedStream = canvas.captureStream(30);
      sourceStream.getAudioTracks().forEach((track) => processedStream.addTrack(track));

      return processedStream;
    },
    []
  );

  return {
    backgroundMode,
    customImageUrl,
    setBackgroundMode,
    applyVirtualBackground,
  };
};
