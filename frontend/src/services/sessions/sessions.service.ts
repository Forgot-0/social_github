import type { PageResult } from '../../types/api/common.ts';
import type { SessionDTO } from '../../types/api/session.ts';
import { apiDelete, apiGet, type QueryParamValue } from '../api/client.ts';

export interface ListSessionsQuery {
  user_id?: number;
  device_id?: string;
  last_activity_after?: string;
  last_activity_before?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listSessions(
  query?: ListSessionsQuery,
): Promise<PageResult<SessionDTO>> {
  return apiGet<PageResult<SessionDTO>>('/sessions/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiDelete(`/sessions/${sessionId}`);
}
