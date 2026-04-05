import type { IHttpClient } from '../application/ports/http-client.port';
import type { PageResult, SessionDTO } from '../domain/types/api.types';

export interface SessionsListQuery {
  user_id?: number;
  device_id?: string;
  last_activity_after?: string;
  last_activity_before?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort?: string;
}

export class SessionsService {
  constructor(private readonly http: IHttpClient) {}

  list(q: SessionsListQuery = {}): Promise<PageResult<SessionDTO>> {
    return this.http.request<PageResult<SessionDTO>>({
      path: '/sessions/',
      method: 'GET',
      query: q,
    });
  }

  delete(sessionId: number): Promise<void> {
    return this.http.request<void>({
      path: `/sessions/${sessionId}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }
}
