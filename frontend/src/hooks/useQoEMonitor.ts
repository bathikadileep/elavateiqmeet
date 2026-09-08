import { useEffect, useRef, useState } from 'react';
import client from '../api/client';

export interface QoEMetrics {
  mos_score: number;
  quality_rating: 'excellent' | 'good' | 'fair' | 'poor' | 'bad';
  rtt_ms: number;
  packet_loss_pct: number;
  jitter_ms: number;
}

export const useQoEMonitor = (peerConnection: RTCPeerConnection | null, roomCode: string) => {
  const [qoe, setQoe] = useState<QoEMetrics | null>(null);
  const intervalRef = useRef<any>(null);

  useEffect(() => {
    if (!peerConnection || !roomCode) return;

    const monitorStats = async () => {
      try {
        const stats = await peerConnection.getStats();
        let rtt = 45.0;
        let loss = 0.2;
        let jitter = 4.0;

        stats.forEach((report) => {
          if (report.type === 'candidate-pair' && report.state === 'succeeded') {
            if (report.currentRoundTripTime) {
              rtt = report.currentRoundTripTime * 1000;
            }
          }
          if (report.type === 'inbound-rtp' && report.kind === 'video') {
            if (report.jitter) jitter = report.jitter * 1000;
            if (report.packetsLost && report.packetsReceived) {
              loss = (report.packetsLost / (report.packetsLost + report.packetsReceived)) * 100;
            }
          }
        });

        const payload = { rtt_ms: rtt, packet_loss_pct: loss, jitter_ms: jitter };
        const res = await client.post('/api/telemetry/report', { room_code: roomCode, stats: payload });
        if (res.data) {
          setQoe(res.data);
        }
      } catch (err) {
        console.warn('QoE monitoring telemetry error:', err);
      }
    };

    intervalRef.current = setInterval(monitorStats, 10000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [peerConnection, roomCode]);

  return qoe;
};
