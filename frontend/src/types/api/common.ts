export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ErrorBody {
  code: string;
  message: string;
  detail: Record<string, unknown> | unknown[] | null;
}

export interface ErrorResponse {
  error: ErrorBody;
  status: number;
  request_id: string;
  timestamp: number;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId: string;
  readonly detail: ErrorBody['detail'];

  constructor(
    message: string,
    opts: {
      code: string;
      status: number;
      requestId: string;
      detail: ErrorBody['detail'];
    },
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = opts.code;
    this.status = opts.status;
    this.requestId = opts.requestId;
    this.detail = opts.detail;
  }
}
