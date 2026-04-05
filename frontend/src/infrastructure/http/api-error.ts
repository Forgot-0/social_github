import type { ErrorResponse } from '../../domain/types/errors.types';

export class ApiError extends Error {
  readonly response: ErrorResponse;

  constructor(response: ErrorResponse) {
    super(response.error.message);
    this.name = 'ApiError';
    this.response = response;
  }
}
