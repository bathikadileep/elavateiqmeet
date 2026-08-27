/**
 * Meeting & Participant Domain Entities
 */

export type MeetingStatus = 'scheduled' | 'live' | 'ended' | 'cancelled';
export type MeetingType = 'instant' | 'scheduled' | 'recurring';
export type ParticipantRole = 'host' | 'co_host' | 'participant' | 'guest';
export type ParticipantStatus = 'invited' | 'joined' | 'left' | 'kicked' | 'declined';

export interface Meeting {
  id: string;
  meeting_code: string;
  title: string;
  description?: string | null;
  host_id: string;
  status: MeetingStatus;
  meeting_type: MeetingType;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  actual_start?: string | null;
  actual_end?: string | null;
  is_locked: boolean;
  is_recorded: boolean;
  chat_enabled: boolean;
  screenshare_enabled: boolean;
  guest_access: boolean;
  max_participants: number;
  created_at: string;
}

export interface MeetingParticipant {
  id: string;
  meeting_id: string;
  user_id?: string | null;
  guest_name?: string | null;
  role: ParticipantRole;
  status: ParticipantStatus;
  is_audio_on: boolean;
  is_video_on: boolean;
  hand_raised: boolean;
  is_screen_sharing: boolean;
  created_at: string;
}
