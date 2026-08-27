import apiClient from './client';
import type { User } from '../types/user';

export interface LoginPayload {
  identity: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export interface AuthResponseData {
  message: string;
  user: User;
  access_token?: string;
}

export interface ForgotPasswordResponseData {
  message: string;
  reset_token?: string;
  reset_url?: string;
}

export const authApi = {
  login: async (payload: LoginPayload): Promise<AuthResponseData> => {
    const response = await apiClient.post<AuthResponseData>('/auth/login', payload);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  },

  register: async (payload: RegisterPayload): Promise<AuthResponseData> => {
    const response = await apiClient.post<AuthResponseData>('/auth/register', payload);
    return response.data;
  },

  logout: async (): Promise<{ message: string }> => {
    try {
      const response = await apiClient.post<{ message: string }>('/auth/logout');
      return response.data;
    } finally {
      localStorage.removeItem('access_token');
    }
  },

  me: async (): Promise<{ user: User }> => {
    const response = await apiClient.get<{ user: User }>('/auth/me');
    return response.data;
  },

  refresh: async (): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/refresh');
    return response.data;
  },

  forgotPassword: async (payload: ForgotPasswordPayload): Promise<ForgotPasswordResponseData> => {
    const response = await apiClient.post<ForgotPasswordResponseData>('/auth/forgot-password', payload);
    return response.data;
  },

  resetPassword: async (payload: ResetPasswordPayload): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/reset-password', payload);
    return response.data;
  },

  changePassword: async (payload: ChangePasswordPayload): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/change-password', payload);
    return response.data;
  },
};

export default authApi;
