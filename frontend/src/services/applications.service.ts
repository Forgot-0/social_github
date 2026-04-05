import type { IHttpClient } from '../application/ports/http-client.port';
import type { ApplicationDTO, PageResult } from '../domain/types/api.types';

export interface ApplicationsListQuery {
  project_id?: number;
  position_id?: string;
  candidate_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface MyApplicationsQuery {
  position_id?: string;
  project_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export class ApplicationsService {
  constructor(private readonly http: IHttpClient) {}

  list(q: ApplicationsListQuery = {}): Promise<PageResult<ApplicationDTO>> {
    return this.http.request<PageResult<ApplicationDTO>>({
      path: '/applications/',
      method: 'GET',
      query: q,
    });
  }

  my(q: MyApplicationsQuery = {}): Promise<PageResult<ApplicationDTO>> {
    return this.http.request<PageResult<ApplicationDTO>>({
      path: '/applications/me',
      method: 'GET',
      query: q,
    });
  }

  approve(applicationId: string): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/applications/${encodeURIComponent(applicationId)}/approve`,
      method: 'POST',
    });
  }

  reject(applicationId: string): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/applications/${encodeURIComponent(applicationId)}/reject`,
      method: 'POST',
    });
  }
}
