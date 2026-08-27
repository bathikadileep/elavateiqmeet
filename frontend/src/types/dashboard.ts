import type { Meeting } from './meeting';

export interface DashboardStats {
  hosted_count: number;
  joined_count: number;
  total_minutes: number;
  total_hours: number;
  unread_notifications: number;
  attendance_rate: number;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  event: 'joined' | 'left' | 'kicked' | 'muted' | 'unmuted';
  event_at: string;
  meeting_id: string;
  user_id?: string | null;
  duration_seconds?: number | null;
}

export interface DashboardOverviewResponse {
  stats: DashboardStats;
  todays_meetings: Meeting[];
  upcoming_meetings: Meeting[];
  notifications: NotificationItem[];
  recent_activity: ActivityItem[];
}
