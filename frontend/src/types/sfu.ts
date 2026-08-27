/**
 * ElevateIQ SFU — TypeScript Type Definitions
 */

export interface SFUTransportOptions {
  id: string;
  iceParameters: {
    usernameFragment: string;
    password: string;
    iceLite: boolean;
  };
  iceCandidates: Array<{
    foundation: string;
    component: number;
    protocol: string;
    priority: number;
    ip: string;
    port: number;
    type: string;
  }>;
  dtlsParameters: {
    role: string;
    fingerprints: Array<{
      algorithm: string;
      value: string;
    }>;
  };
}

export interface SFUProducer {
  id: string;
  kind: 'audio' | 'video';
  paused: boolean;
}

export interface SFUConsumer {
  id: string;
  producerId: string;
  kind: 'audio' | 'video';
  paused: boolean;
  spatialLayer: number;
}

export interface VADState {
  activeSpeakerSid: string | null;
  activeSpeakerName: string | null;
  audioLevelDbfs: number;
  audioLevelPercent: number;
  isSpeaking: boolean;
}

export interface WebRTCHealthMetrics {
  rttMs: number;
  packetLossPercent: number;
  audioBitrateKbps: number;
  videoBitrateKbps: number;
  framerateFps: number;
  resolution: string;
  simulcastLayer: 'high' | 'medium' | 'low';
  score: number;
}
