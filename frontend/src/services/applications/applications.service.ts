import type { PageResult } from '../../types/api/common.ts';
import type { ApplicationDTO } from '../../types/api/application.ts';
import { apiGet, apiPost, type QueryParamValue } from '../api/client.ts';

export interface ListApplicationsQuery {
  project_id?: number;
  position_id?: string;
  candidate_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listApplications(
  query?: ListApplicationsQuery,
): Promise<PageResult<ApplicationDTO>> {
  return apiGet<PageResult<ApplicationDTO>>('/applications/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export interface ListMyApplicationsQuery {
  position_id?: string;
  project_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listMyApplications(
  query?: ListMyApplicationsQuery,
): Promise<PageResult<ApplicationDTO>> {
  return apiGet<PageResult<ApplicationDTO>>('/applications/me', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function approveApplication(applicationId: string): Promise<void> {
  await apiPost<unknown>(
    `/applications/${encodeURIComponent(applicationId)}/approve`,
    { body: {} },
  );
}

export async function rejectApplication(applicationId: string): Promise<void> {
  await apiPost<unknown>(
    `/applications/${encodeURIComponent(applicationId)}/reject`,
    { body: {} },
  );
}
