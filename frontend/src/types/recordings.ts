/**
 * ElevateIQ Cloud Recording & HLS Streaming — TypeScript Definitions
 */

export interface MeetingRecordingItem {
  id: string;
  meeting_id: string;
  status: 'processing' | 'available' | 'failed' | 'deleted';
  started_at: string;
  duration_seconds: number;
  download_url: string;
  size_bytes?: number;
  hls_playlist_url?: string;
}
