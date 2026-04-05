import { ApiError } from '../../types/api/common.ts';

export function isApiError(e: unknown): e is ApiError {
  return e instanceof ApiError;
}
