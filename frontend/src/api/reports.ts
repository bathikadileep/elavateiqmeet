import apiClient from './client';
import type {
  AttendanceReportRecord,
  MeetingReportRecord,
  UserActivityReportRecord,
} from '../types/reports';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1';

export const reportsApi = {
  getAttendanceReport: async (meetingId?: string): Promise<{ data: AttendanceReportRecord[] }> => {
    const url = meetingId ? `/reports/attendance?meeting_id=${meetingId}` : '/reports/attendance';
    const response = await apiClient.get<{ data: AttendanceReportRecord[] }>(url);
    return response.data;
  },

  getMeetingReport: async (): Promise<{ data: MeetingReportRecord[] }> => {
    const response = await apiClient.get<{ data: MeetingReportRecord[] }>('/reports/meetings');
    return response.data;
  },

  getUserActivityReport: async (): Promise<{ data: UserActivityReportRecord[] }> => {
    const response = await apiClient.get<{ data: UserActivityReportRecord[] }>('/reports/user-activity');
    return response.data;
  },

  getExportUrl: (reportType: 'attendance' | 'meetings' | 'user-activity', format: 'csv' | 'excel') => {
    return `${BASE_URL}/reports/${reportType}?format=${format}`;
  },
};

export default reportsApi;
