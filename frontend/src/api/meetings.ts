import apiClient from './client';
import type { Meeting } from '../types/meeting';

export interface CreateMeetingPayload {
  title?: string;
  description?: string;
  meeting_type?: 'instant' | 'scheduled' | 'recurring';
  scheduled_start?: string;
  scheduled_end?: string;
  max_participants?: number;
  password?: string;
}

export interface UpdateMeetingPayload {
  title?: string;
  description?: string;
  max_participants?: number;
}

export interface InvitePayload {
  emails?: string[];
  usernames?: string[];
}

export interface InviteResponse {
  message: string;
  invited_count: number;
  meeting_code: string;
  join_url: string;
}

export interface MeetingHistoryItem extends Meeting {
  is_host: boolean;
}

export const meetingsApi = {
  create: async (payload: CreateMeetingPayload = {}): Promise<{ message: string; meeting: Meeting }> => {
    const response = await apiClient.post<{ message: string; meeting: Meeting }>('/meetings', payload);
    return response.data;
  },

  list: async (status?: string): Promise<{ meetings: Meeting[] }> => {
    const url = status ? `/meetings?status=${status}` : '/meetings';
    const response = await apiClient.get<{ meetings: Meeting[] }>(url);
    return response.data;
  },

  getByCode: async (code: string): Promise<{ meeting: Meeting }> => {
    const response = await apiClient.get<{ meeting: Meeting }>(`/meetings/code/${code}`);
    return response.data;
  },

  getHistory: async (): Promise<{ meetings: MeetingHistoryItem[] }> => {
    const response = await apiClient.get<{ meetings: MeetingHistoryItem[] }>('/meetings/history');
    return response.data;
  },

  getDetails: async (id: string): Promise<{ meeting: Meeting }> => {
    const response = await apiClient.get<{ meeting: Meeting }>(`/meetings/${id}`);
    return response.data;
  },

  update: async (id: string, payload: UpdateMeetingPayload): Promise<{ message: string; meeting: Meeting }> => {
    const response = await apiClient.put<{ message: string; meeting: Meeting }>(`/meetings/${id}`, payload);
    return response.data;
  },

  delete: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/meetings/${id}`);
    return response.data;
  },

  invite: async (id: string, payload: InvitePayload): Promise<InviteResponse> => {
    const response = await apiClient.post<InviteResponse>(`/meetings/${id}/invite`, payload);
    return response.data;
  },
};

export default meetingsApi;
