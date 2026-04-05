import { ApiError, type ErrorResponse } from '../../types/api/common.ts';

export type QueryParamValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Array<string | number | boolean>;

export function buildQueryString(
  params?: Record<string, QueryParamValue>,
): string {
  if (!params) return '';
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const v of value) {
        if (v !== undefined && v !== null) sp.append(key, String(v));
      }
    } else {
      sp.append(key, String(value));
    }
  }
  const s = sp.toString();
  return s ? `?${s}` : '';
}

let baseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1').replace(
  /\/$/,
  '',
);
let getAccessToken: () => string | null = () => null;

export interface ApiClientConfig {
  baseUrl?: string;
  getAccessToken?: () => string | null;
}

export function configureApiClient(config: ApiClientConfig): void {
  if (config.baseUrl !== undefined) {
    baseUrl = config.baseUrl.replace(/\/$/, '');
  }
  if (config.getAccessToken !== undefined) {
    getAccessToken = config.getAccessToken;
  }
}

export function getApiBaseUrl(): string {
  return baseUrl;
}

export function apiPath(
  path: string,
  query?: Record<string, QueryParamValue>,
): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${p}${buildQueryString(query)}`;
}

/** Absolute URL for browser navigation (OAuth, downloads). */
export function resolveApiUrl(
  path: string,
  query?: Record<string, QueryParamValue>,
): string {
  const rel = apiPath(path, query);
  if (rel.startsWith('http://') || rel.startsWith('https://')) {
    return rel;
  }
  if (typeof globalThis !== 'undefined' && 'location' in globalThis) {
    const loc = (globalThis as { location?: { origin: string } }).location;
    if (loc?.origin) {
      return new URL(rel, loc.origin).href;
    }
  }
  return rel;
}

function authHeaders(): Headers {
  const headers = new Headers();
  const t = getAccessToken();
  if (t) headers.set('Authorization', `Bearer ${t}`);
  return headers;
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = (await res.json()) as ErrorResponse;
    const e = body.error;
    return new ApiError(e?.message ?? res.statusText, {
      code: e?.code ?? 'UNKNOWN',
      status: body.status ?? res.status,
      requestId: body.request_id ?? '',
      detail: e?.detail ?? null,
    });
  } catch {
    return new ApiError(res.statusText, {
      code: 'UNKNOWN',
      status: res.status,
      requestId: '',
      detail: null,
    });
  }
}

async function parseBody<T>(res: Response): Promise<T> {
  if (res.status === 204) {
    return undefined as T;
  }
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  const ct = res.headers.get('content-type') ?? '';
  if (ct.includes('application/json')) {
    return JSON.parse(text) as T;
  }
  return text as unknown as T;
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  query?: Record<string, QueryParamValue>;
  body?: unknown;
  /** Attach Bearer token when true (default). */
  auth?: boolean;
}

export async function apiRequest<T>(
  method: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { query, body, auth = true, headers: initHeaders, ...rest } = options;
  const headers = auth ? authHeaders() : new Headers();
  if (initHeaders) {
    new Headers(initHeaders).forEach((v, k) => headers.set(k, v));
  }
  let reqBody: BodyInit | undefined;
  if (body !== undefined) {
    headers.set('Content-Type', 'application/json');
    reqBody = JSON.stringify(body);
  }
  const res = await fetch(apiPath(path, query), {
    method,
    credentials: 'include',
    headers,
    body: reqBody,
    ...rest,
  });
  if (!res.ok) {
    throw await parseError(res);
  }
  return parseBody<T>(res);
}

export async function apiGet<T>(
  path: string,
  options: Omit<RequestOptions, 'body'> = {},
): Promise<T> {
  return apiRequest<T>('GET', path, options);
}

export async function apiPost<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return apiRequest<T>('POST', path, options);
}

export async function apiPut<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return apiRequest<T>('PUT', path, options);
}

export async function apiDelete(
  path: string,
  options: RequestOptions = {},
): Promise<void> {
  await apiRequest<unknown>('DELETE', path, options);
}

export async function apiPostForm<T>(
  path: string,
  data: Record<string, string>,
  options: Omit<RequestOptions, 'body'> = {},
): Promise<T> {
  const { auth = false, headers: initHeaders, ...rest } = options;
  const headers = auth ? authHeaders() : new Headers();
  if (initHeaders) {
    new Headers(initHeaders).forEach((v, k) => headers.set(k, v));
  }
  headers.set('Content-Type', 'application/x-www-form-urlencoded');
  const res = await fetch(apiPath(path), {
    method: 'POST',
    credentials: 'include',
    headers,
    body: new URLSearchParams(data),
    ...rest,
  });
  if (!res.ok) {
    throw await parseError(res);
  }
  return parseBody<T>(res);
}

export function httpToWebSocketUrl(httpUrl: string): string {
  return httpUrl
    .replace(/^https:\/\//i, 'wss://')
    .replace(/^http:\/\//i, 'ws://');
}

export function buildChatWebSocketUrl(accessToken: string): string {
  const httpUrl = resolveApiUrl('/chats/ws/', { token: accessToken });
  return httpToWebSocketUrl(httpUrl);
}

/** GET with Bearer; on 302/307 assigns window.location to Location (OAuth connect). */
export async function followAuthRedirectGet(path: string): Promise<void> {
  const res = await fetch(apiPath(path), {
    method: 'GET',
    credentials: 'include',
    redirect: 'manual',
    headers: authHeaders(),
  });
  const loc = res.headers.get('Location');
  if ((res.status === 307 || res.status === 302) && loc) {
    window.location.href = loc;
    return;
  }
  if (!res.ok) {
    throw await parseError(res);
  }
}
