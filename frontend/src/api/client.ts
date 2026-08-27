import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { ApiError, type ApiErrorResponse } from '../types/api';

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${host}:5000/api/v1`;
};

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: true, // Required for HttpOnly JWT session cookies
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Auto-refresh 401 & Map Error Envelopes
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse | { error?: string }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized token refresh (only if user was previously authenticated)
    const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('access_token');
    if (
      error.response?.status === 401 &&
      hasToken &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register') &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => apiClient(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await apiClient.post('/auth/refresh');
        isRefreshing = false;
        processQueue(null);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        isRefreshing = false;
        processQueue(refreshErr, null);
        window.dispatchEvent(new Event('auth-expired'));
        return Promise.reject(parseApiError(error));
      }
    }

    return Promise.reject(parseApiError(error));
  }
);

/**
 * Normalizes Axios errors into typed ApiError instances
 */
export function parseApiError(error: AxiosError<ApiErrorResponse | { error?: string }>): ApiError {
  if (error.response?.data) {
    const data = error.response.data;

    // Check backend JSON envelope format
    if ('error' in data && typeof data.error === 'object' && data.error !== null) {
      return new ApiError({
        code: data.error.code || 'UNKNOWN_ERROR',
        message: data.error.message || 'An unexpected error occurred.',
        status: data.error.status || error.response.status || 500,
        details: data.error.details,
      });
    }

    // Fallback string error format
    if ('error' in data && typeof data.error === 'string') {
      return new ApiError({
        code: 'BAD_REQUEST',
        message: data.error,
        status: error.response.status || 400,
      });
    }
  }

  // Network / server offline
  if (error.request && !error.response) {
    return new ApiError({
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to ElevateIQ servers. Please check your connection.',
      status: 0,
    });
  }

  return new ApiError({
    code: 'UNKNOWN_ERROR',
    message: error.message || 'An unexpected error occurred.',
    status: error.response?.status || 500,
  });
}

export default apiClient;
