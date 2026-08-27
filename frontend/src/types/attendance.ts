import type { Meeting } from './meeting';

export interface AttendanceSummary {
  total_joined: number;
  total_hosted: number;
  total_minutes: number;
  total_hours: number;
  avg_duration_minutes: number;
  attendance_percentage: number;
  on_time_rate: number;
}

export interface ParticipantRosterItem {
  participant_id: string;
  user_id?: string | null;
  name: string;
  email: string;
  role: string;
  status: string;
  join_time: string;
  leave_time?: string | null;
  duration_seconds: number;
  duration_minutes: number;
  attendance_percentage: number;
}

export interface MeetingAttendanceReportResponse {
  meeting: Meeting;
  total_participants: number;
  roster: ParticipantRosterItem[];
}

export interface UserAttendanceLogItem {
  id: string;
  meeting_id: string;
  meeting_title: string;
  meeting_code: string;
  event: string;
  event_at: string;
  duration_seconds?: number | null;
  duration_minutes: number;
}
