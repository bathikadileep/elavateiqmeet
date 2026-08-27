export interface AdminMetrics {
  total_users: number;
  active_users: number;
  suspended_users: number;
  total_meetings: number;
  live_meetings: number;
  scheduled_meetings: number;
  total_files: number;
  total_storage_mb: number;
  total_platform_hours: number;
}

export interface GrowthSeriesPoint {
  label: string;
  users: number;
  meetings: number;
}

export interface AdminAnalyticsResponse {
  metrics: AdminMetrics;
  growth_series: GrowthSeriesPoint[];
}

export interface AdminUserItem {
  id: string;
  username: string;
  email: string;
  display_name?: string | null;
  status: string;
  roles: string[];
  created_at: string;
}

export interface AdminMeetingItem {
  id: string;
  meeting_code: string;
  title: string;
  host_id?: string | null;
  host_name: string;
  status: string;
  meeting_type: string;
  max_participants: number;
  created_at: string;
}

export interface AdminRoleItem {
  id: string;
  name: string;
  description?: string | null;
  is_system: boolean;
  permissions: string[];
}
