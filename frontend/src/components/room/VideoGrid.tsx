import React from 'react';
import ParticipantCard from './ParticipantCard';
import type { PeerStream } from '../../types/webrtc';

export interface VideoGridProps {
  streams: PeerStream[];
}

export const VideoGrid: React.FC<VideoGridProps> = ({ streams }) => {
  // Determine optimal responsive grid column layout
  const getGridColsClass = (count: number) => {
    if (count <= 1) return 'grid-cols-1 max-w-4xl mx-auto h-[calc(100vh-10rem)]';
    if (count === 2) return 'grid-cols-1 md:grid-cols-2 max-w-6xl mx-auto h-[calc(100vh-10rem)]';
    if (count <= 4) return 'grid-cols-1 sm:grid-cols-2 max-w-6xl mx-auto h-[calc(100vh-10rem)]';
    if (count <= 6) return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
    return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4';
  };

  return (
    <div className={`w-full h-full p-4 grid gap-4 items-center justify-center overflow-y-auto ${getGridColsClass(streams.length)}`}>
      {streams.map((peer) => (
        <ParticipantCard key={peer.sid} peer={peer} />
      ))}
    </div>
  );
};

export default VideoGrid;
