import { useState, useCallback } from 'react';

export interface PeerPosition {
  peerId: string;
  x: number;
  y: number;
  z: number;
}

export const useSpatialAudio = () => {
  const [positions, setPositions] = useState<Record<string, PeerPosition>>({});

  const updatePeerPosition = useCallback((peerId: string, x: number, y: number, z: number = 0) => {
    setPositions(prev => ({
      ...prev,
      [peerId]: { peerId, x, y, z },
    }));
  }, []);

  return { positions, updatePeerPosition };
};
