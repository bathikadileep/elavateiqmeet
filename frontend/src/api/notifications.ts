import apiClient from './client';
import type { NotificationItem } from '../types/notifications';

export const notificationsApi = {
  list: async (): Promise<{ unread_count: number; notifications: NotificationItem[] }> => {
    const response = await apiClient.get<{ unread_count: number; notifications: NotificationItem[] }>('/notifications');
    return response.data;
  },

  markRead: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(`/notifications/${id}/read`);
    return response.data;
  },

  markAllRead: async (): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>('/notifications/read-all');
    return response.data;
  },

  send: async (payload: {
    recipient_id: string;
    notif_type?: string;
    title: string;
    body?: string;
    send_email?: boolean;
  }): Promise<{ message: string; notification: NotificationItem }> => {
    const response = await apiClient.post<{ message: string; notification: NotificationItem }>('/notifications/send', payload);
    return response.data;
  },
};

export default notificationsApi;
