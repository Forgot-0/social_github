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

export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}
