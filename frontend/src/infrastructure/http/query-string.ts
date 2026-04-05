import type { QueryPrimitive } from '../../application/ports/http-client.port';

export function appendQuery(
  params: URLSearchParams,
  key: string,
  value: QueryPrimitive | null | undefined,
): void {
  if (value === undefined || value === null) return;
  params.append(key, String(value));
}

export function appendQueryMulti(
  params: URLSearchParams,
  key: string,
  values: readonly (string | number)[] | null | undefined,
): void {
  if (!values?.length) return;
  for (const v of values) {
    params.append(key, String(v));
  }
}
