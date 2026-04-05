import type {
  HttpRequestOptions,
  IHttpClient,
} from '../../application/ports/http-client.port';
import type { ErrorResponse } from '../../domain/types/errors.types';
import { ApiError } from './api-error';
import { appendQuery, appendQueryMulti } from './query-string';

export interface FetchHttpClientOptions {
  /** API prefix including `/api/v1`, e.g. `/api/v1` or `https://api.example.com/api/v1`. */
  basePath: string;
  getAccessToken?: () => string | null;
  credentials?: RequestCredentials;
}

function joinBasePath(basePath: string, path: string): string {
  const b = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

export function createFetchHttpClient(
  options: FetchHttpClientOptions,
): IHttpClient {
  const { basePath, getAccessToken, credentials = 'include' } = options;

  return {
    async request<T>(opts: HttpRequestOptions): Promise<T> {
      const params = new URLSearchParams();
      if (opts.query) {
        for (const [k, v] of Object.entries(opts.query)) {
          if (v === undefined || v === null) continue;
          if (
            typeof v === 'string' ||
            typeof v === 'number' ||
            typeof v === 'boolean'
          ) {
            appendQuery(params, k, v);
          }
        }
      }
      if (opts.queryMulti) {
        for (const [k, arr] of Object.entries(opts.queryMulti)) {
          appendQueryMulti(params, k, arr ?? undefined);
        }
      }

      const qs = params.toString();
      const url = `${joinBasePath(basePath, opts.path)}${qs ? `?${qs}` : ''}`;

      const headers = new Headers();
      if (opts.formUrlEncoded) {
        headers.set('Content-Type', 'application/x-www-form-urlencoded');
      } else if (opts.jsonBody !== undefined && opts.method !== 'GET') {
        headers.set('Content-Type', 'application/json');
      }

      const token = getAccessToken?.();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }

      const res = await fetch(url, {
        method: opts.method,
        headers,
        body:
          opts.formUrlEncoded ??
          (opts.jsonBody !== undefined
            ? JSON.stringify(opts.jsonBody)
            : undefined),
        credentials,
      });

      const parseAs = opts.parseAs ?? 'json';

      if (!res.ok) {
        let errBody: ErrorResponse | null = null;
        try {
          errBody = (await res.json()) as ErrorResponse;
        } catch {
          /* ignore */
        }
        if (errBody?.error) {
          throw new ApiError(errBody);
        }
        throw new Error(`HTTP ${res.status} ${res.statusText}`);
      }

      if (res.status === 204 || parseAs === 'void') {
        return undefined as T;
      }

      if (parseAs === 'text') {
        return (await res.text()) as T;
      }

      const contentType = res.headers.get('content-type') ?? '';
      const raw = await res.text();
      if (!raw) {
        return undefined as T;
      }
      if (contentType.includes('application/json')) {
        return JSON.parse(raw) as T;
      }
      return raw as T;
    },
  };
}

export function resolveApiBasePath(): string {
  const root = import.meta.env.VITE_API_BASE_URL ?? '';
  const trimmed = root.endsWith('/') ? root.slice(0, -1) : root;
  return `${trimmed}/api/v1`;
}
