/**
 * Axios Instance with automatic token refresh
 * 
 * SECURITY FEATURES:
 * - Access token in Authorization header
 * - Automatic refresh on 401/403 with INVALID_TOKEN or EXPIRED_TOKEN
 * - Single refresh in flight (request queue)
 * - Credentials included for refresh cookie
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiError, AccessTokenResponse } from './types';
import { tokenManager } from './tokenManager';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance
export const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // ВАЖНО: включаем credentials для отправки HttpOnly cookie
  withCredentials: true,
});

// Request queue for handling parallel requests during refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Request Interceptor - добавляет access token
 */
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken();
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor - обрабатывает ошибки и автоматический refresh
 */
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Проверяем нужен ли refresh
    const shouldRefresh =
      error.response?.status === 400 &&
      error.response?.data?.error?.code === 'EXPIRED_TOKEN';

    const shouldRefreshAlt =
      error.response?.status === 403 &&
      error.response?.data?.error?.code === 'INVALID_TOKEN';

    if ((shouldRefresh || shouldRefreshAlt) && !originalRequest._retry) {
      if (isRefreshing) {
        // Если refresh уже в процессе, добавляем запрос в очередь
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Вызываем refresh endpoint
        const response = await axios.post<AccessTokenResponse>(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          {},
          {
            withCredentials: true, // КРИТИЧНО: отправляем refresh cookie
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        const { access_token } = response.data;

        // Сохраняем новый access token В ПАМЯТИ
        tokenManager.setAccessToken(access_token);

        // Обрабатываем очередь запросов
        processQueue(null, access_token);

        // Повторяем оригинальный запрос с новым токеном
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed - пользователь должен перелогиниться
        processQueue(refreshError, null);
        tokenManager.clearAccessToken();
        
        // Можно тут вызвать logout или редирект на /login
        // window.location.href = '/login';
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Helper function для форматирования query parameters
 */
export const formatQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        // Для массивов добавляем каждый элемент
        value.forEach((item) => searchParams.append(key, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  return searchParams.toString();
};
