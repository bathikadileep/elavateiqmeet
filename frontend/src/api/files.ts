import apiClient from './client';
import type { FileItem } from '../types/files';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1';

export const filesApi = {
  upload: async (file: File, meetingId?: string, category?: string): Promise<{ message: string; file: FileItem }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (meetingId) formData.append('meeting_id', meetingId);
    if (category) formData.append('file_category', category);

    const response = await apiClient.post<{ message: string; file: FileItem }>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  list: async (meetingId?: string, category?: string): Promise<{ files: FileItem[] }> => {
    let url = '/files';
    const params = new URLSearchParams();
    if (meetingId) params.append('meeting_id', meetingId);
    if (category) params.append('category', category);
    if (params.toString()) url += `?${params.toString()}`;

    const response = await apiClient.get<{ files: FileItem[] }>(url);
    return response.data;
  },

  delete: async (fileId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/files/${fileId}`);
    return response.data;
  },

  getDownloadUrl: (fileId: string) => `${BASE_URL}/files/${fileId}/download`,
  getPreviewUrl: (fileId: string) => `${BASE_URL}/files/${fileId}/preview`,
};

export default filesApi;
