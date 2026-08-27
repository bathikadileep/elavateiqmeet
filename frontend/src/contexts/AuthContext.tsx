import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authApi, {
  type LoginPayload,
  type RegisterPayload,
  type ForgotPasswordPayload,
  type ResetPasswordPayload,
  type ChangePasswordPayload,
  type ForgotPasswordResponseData,
} from '../api/auth';
import type { User } from '../types/user';
import { ApiError } from '../types/api';

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
  forgotPassword: (payload: ForgotPasswordPayload) => Promise<ForgotPasswordResponseData>;
  resetPassword: (payload: ResetPasswordPayload) => Promise<void>;
  changePassword: (payload: ChangePasswordPayload) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshUser = useCallback(async () => {
    try {
      const data = await authApi.me();
      setUser(data.user);
      setError(null);
    } catch {
      setUser(null);
    }
  }, []);

  // Initialize and verify user session on app mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const data = await authApi.me();
        setUser(data.user);
      } catch {
        setUser(null);
        localStorage.removeItem('access_token');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    // Listen for automatic token expiration broadcast from Axios interceptor
    const handleAuthExpired = () => {
      const hadToken = !!localStorage.getItem('access_token');
      localStorage.removeItem('access_token');
      setUser(null);
      if (hadToken) {
        setError('Your session has expired. Please log in again.');
      }
    };

    window.addEventListener('auth-expired', handleAuthExpired);
    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
    };
  }, []);

  const login = async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await authApi.login(payload);
      setUser(data.user);
    } catch (err) {
      setUser(null);
      const apiErr = err as ApiError;
      const msg = apiErr.message || 'Login failed. Please check your credentials.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.register(payload);
    } catch (err) {
      const apiErr = err as ApiError;
      const msg = apiErr.message || 'Registration failed. Please try again.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } catch (err) {
      console.warn('Logout request completed with warning:', err);
    } finally {
      setUser(null);
      setError(null);
      setIsLoading(false);
    }
  };

  const forgotPassword = async (payload: ForgotPasswordPayload) => {
    setError(null);
    try {
      return await authApi.forgotPassword(payload);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message || 'Forgot password request failed.');
      throw err;
    }
  };

  const resetPassword = async (payload: ResetPasswordPayload) => {
    setError(null);
    try {
      await authApi.resetPassword(payload);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message || 'Password reset failed.');
      throw err;
    }
  };

  const changePassword = async (payload: ChangePasswordPayload) => {
    setError(null);
    try {
      await authApi.changePassword(payload);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message || 'Password change failed.');
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
        refreshUser,
        forgotPassword,
        resetPassword,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
