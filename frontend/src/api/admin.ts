import apiClient from './client';
import type {
  AdminAnalyticsResponse,
  AdminUserItem,
  AdminMeetingItem,
  AdminRoleItem,
} from '../types/admin';

export const adminApi = {
  getAnalytics: async (): Promise<AdminAnalyticsResponse> => {
    const response = await apiClient.get<AdminAnalyticsResponse>('/admin/analytics');
    return response.data;
  },

  listUsers: async (query?: string, status?: string): Promise<{ users: AdminUserItem[] }> => {
    let url = '/admin/users';
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (status) params.append('status', status);
    if (params.toString()) url += `?${params.toString()}`;

    const response = await apiClient.get<{ users: AdminUserItem[] }>(url);
    return response.data;
  },

  updateUserStatus: async (userId: string, status: string): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(`/admin/users/${userId}/status`, { status });
    return response.data;
  },

  updateUserRoles: async (userId: string, roles: string[]): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(`/admin/users/${userId}/roles`, { roles });
    return response.data;
  },

  deleteUser: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/admin/users/${userId}`);
    return response.data;
  },

  listMeetings: async (): Promise<{ meetings: AdminMeetingItem[] }> => {
    const response = await apiClient.get<{ meetings: AdminMeetingItem[] }>('/admin/meetings');
    return response.data;
  },

  forceEndMeeting: async (meetingId: string): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(`/admin/meetings/${meetingId}/end`);
    return response.data;
  },

  deleteMeeting: async (meetingId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/admin/meetings/${meetingId}`);
    return response.data;
  },

  listRoles: async (): Promise<{ roles: AdminRoleItem[] }> => {
    const response = await apiClient.get<{ roles: AdminRoleItem[] }>('/admin/roles');
    return response.data;
  },
};

export default adminApi;
