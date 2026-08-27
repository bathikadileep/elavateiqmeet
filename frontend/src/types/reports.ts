export interface AttendanceReportRecord {
  id: string;
  meeting_title: string;
  participant: string;
  event: string;
  event_at: string;
  duration_minutes: number;
  status: string;
}

export interface MeetingReportRecord {
  id: string;
  meeting_code: string;
  title: string;
  host_name: string;
  meeting_type: string;
  status: string;
  participant_count: number;
  created_at: string;
}

export interface UserActivityReportRecord {
  id: string;
  username: string;
  email: string;
  display_name: string;
  status: string;
  hosted_count: number;
  joined_count: number;
  active_hours: number;
  created_at: string;
}
