import apiClient from './client';
import type { DashboardOverviewResponse, NotificationItem } from '../types/dashboard';

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverviewResponse> => {
    const response = await apiClient.get<DashboardOverviewResponse>('/dashboard/overview');
    return response.data;
  },

  markNotificationRead: async (id: string): Promise<{ message: string; notification: NotificationItem }> => {
    const response = await apiClient.post<{ message: string; notification: NotificationItem }>(
      `/dashboard/notifications/${id}/read`
    );
    return response.data;
  },
};

export default dashboardApi;
