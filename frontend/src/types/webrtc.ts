export interface PeerStream {
  sid: string;
  userId?: string | null;
  name: string;
  stream: MediaStream | null;
  isLocal: boolean;
  isAudioMuted: boolean;
  isVideoOff: boolean;
  isScreenSharing: boolean;
  handRaised: boolean;
}

export interface PeerMediaState {
  sid: string;
  userId?: string | null;
  is_audio_muted: boolean;
  is_video_off: boolean;
  is_screen_sharing: boolean;
  hand_raised: boolean;
}
