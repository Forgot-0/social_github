/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * База API (без завершающего `/`).
   * Локально по умолчанию `/api/v1` (через Vite proxy → тот же origin, cookie strict).
   * Прод: фронт `https://incollab.ru`, API `https://api.incollab.ru` →
   * `VITE_API_BASE_URL=https://api.incollab.ru/api/v1`
   */
  readonly VITE_API_BASE_URL?: string;
  /** Бэкенд для dev-proxy `/api` (cookie SameSite=strict с фронтом на том же origin). */
  readonly VITE_API_PROXY_TARGET?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
