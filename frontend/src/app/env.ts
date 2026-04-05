export interface AppEnv {
  readonly apiBaseUrl: string;
  readonly appName: string;
}

function sanitizeApiBaseUrl(value: string | undefined): string {
  const raw = (value ?? '').trim();
  if (!raw) {
    return '/api/v1';
  }

  if (raw.endsWith('/api/v1')) {
    return raw;
  }

  return `${raw.replace(/\/$/, '')}/api/v1`;
}

export const appEnv: AppEnv = {
  apiBaseUrl: sanitizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL),
  appName: (import.meta.env.VITE_APP_NAME ?? 'Social GitHub').trim(),
};
