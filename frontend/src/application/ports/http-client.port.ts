export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export type QueryPrimitive = string | number | boolean;

export interface HttpRequestOptions {
  path: string;
  method: HttpMethod;
  /** Simple query params (scalar values). Plain objects from typed filters are accepted. */
  query?: Record<string, QueryPrimitive | null | undefined> | object;
  /** Repeated query keys, e.g. `role_names=admin&role_names=member`. */
  queryMulti?: Record<string, readonly (string | number)[] | null | undefined>;
  jsonBody?: unknown;
  formUrlEncoded?: URLSearchParams;
  /** Use when the response is not JSON (e.g. plain `"OK"`). */
  parseAs?: 'json' | 'text' | 'void';
}

export interface IHttpClient {
  request<T>(options: HttpRequestOptions): Promise<T>;
}
