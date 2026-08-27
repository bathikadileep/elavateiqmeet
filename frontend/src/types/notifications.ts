export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body?: string | null;
  metadata?: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}
