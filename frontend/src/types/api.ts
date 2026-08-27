/**
 * Standardized API Response & Error Envelopes
 * Matches backend Flask core error handling format
 */

export interface ApiErrorDetail {
  [key: string]: string | string[] | number | boolean;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  status: number;
  details?: ApiErrorDetail;
}

export interface ApiErrorResponse {
  error: ApiErrorPayload;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: ApiErrorDetail;

  constructor(payload: ApiErrorPayload) {
    super(payload.message);
    self.name = 'ApiError';
    this.code = payload.code;
    this.status = payload.status;
    this.details = payload.details;
  }
}

export interface ApiResponse<T = unknown> {
  message?: string;
  data?: T;
}
