import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { tokenManager } from "@/lib/auth/token-manager";

interface AccessTokenResponse {
  access_token: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// ─── Request interceptor: прикрепляем Authorization header ───────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenManager.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response interceptor: автоматический refresh при ошибках аутентификации ─
//
// Бэкенд использует разные HTTP-коды для разных ситуаций:
//   400 + INVALID_TOKEN  — токен невалиден (jwt_manager.validate_token)
//   400 + EXPIRED_TOKEN  — токен истёк
//   401                  — не аутентифицирован (NotAuthenticatedException)
//   403 без ACCESS_DENIED — HTTPBearer: отсутствует Authorization header
//   403 + ACCESS_DENIED  — RBAC: нет прав (refresh НЕ поможет)

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  for (const promise of failedQueue) {
    if (token) {
      promise.resolve(token);
    } else {
      promise.reject(error);
    }
  }
  failedQueue = [];
}

const AUTH_ERROR_CODES = new Set(["INVALID_TOKEN", "EXPIRED_TOKEN", "NOT_AUTHNTICATED"]);

function shouldRefresh(error: AxiosError): boolean {
  const status = error.response?.status;
  const data = error.response?.data as Record<string, unknown> | undefined;
  const errorObj = (data?.error ?? data) as Record<string, unknown> | undefined;
  const code = errorObj?.code as string | undefined;

  // 400 — только если код ошибки связан с токеном
  if (status === 400 && code && AUTH_ERROR_CODES.has(code)) return true;

  // 401 — всегда пробуем refresh
  if (status === 401) return true;

  // 403 — только если это НЕ ошибка прав доступа (ACCESS_DENIED = RBAC, refresh не поможет)
  if (status === 403 && code !== "ACCESS_DENIED") return true;

  return false;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (!shouldRefresh(error) || originalRequest._retry) {
      return Promise.reject(error);
    }

    const url = originalRequest.url ?? "";
    if (url.includes("/auth/refresh") || url.includes("/auth/login") || url.includes("/auth/logout")) {
      tokenManager.clearToken();
      return Promise.reject(error);
    }

    if (tokenManager.getToken() != null) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<AccessTokenResponse>(
        `${API_BASE_URL}/v1/auth/refresh`,
        {},
        { withCredentials: true },
      );

      const newToken = data.access_token;
      tokenManager.setToken(newToken);
      processQueue(null, newToken);

      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      tokenManager.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
