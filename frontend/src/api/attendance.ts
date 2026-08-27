import apiClient from './client';
import type {
  AttendanceSummary,
  MeetingAttendanceReportResponse,
  UserAttendanceLogItem,
} from '../types/attendance';

export const attendanceApi = {
  getSummary: async (): Promise<AttendanceSummary> => {
    const response = await apiClient.get<AttendanceSummary>('/attendance/summary');
    return response.data;
  },

  getMeetingReport: async (meetingId: string): Promise<MeetingAttendanceReportResponse> => {
    const response = await apiClient.get<MeetingAttendanceReportResponse>(`/attendance/meetings/${meetingId}`);
    return response.data;
  },

  getUserLogs: async (): Promise<{ logs: UserAttendanceLogItem[] }> => {
    const response = await apiClient.get<{ logs: UserAttendanceLogItem[] }>('/attendance/user');
    return response.data;
  },

  logEvent: async (payload: { meeting_id: string; event: 'joined' | 'left'; duration_seconds?: number }): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/attendance/log', payload);
    return response.data;
  },
};

export default attendanceApi;
