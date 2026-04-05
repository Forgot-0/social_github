import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  ApplicationDTO,
  PageResult,
  PositionDTO,
} from '../domain/types/api.types';

export interface PositionsListQuery {
  project_id?: number;
  title?: string;
  required_skills?: readonly string[];
  is_open?: boolean;
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface PositionApplicationsQuery {
  project_id?: number;
  candidate_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export class PositionsService {
  constructor(private readonly http: IHttpClient) {}

  list(q: PositionsListQuery = {}): Promise<PageResult<PositionDTO>> {
    const { required_skills, page, page_size, sort, ...rest } = q;
    return this.http.request<PageResult<PositionDTO>>({
      path: '/positions/',
      method: 'GET',
      query: { ...rest, page, page_size, sort },
      queryMulti: { required_skills },
    });
  }

  get(positionId: string): Promise<PositionDTO> {
    return this.http.request<PositionDTO>({
      path: `/positions/${encodeURIComponent(positionId)}`,
      method: 'GET',
    });
  }

  update(
    positionId: string,
    body: {
      title?: string;
      description?: string;
      responsibilities?: string | null;
      required_skills?: string[];
      location_type?: 'remote' | 'onsite' | 'hybrid';
      expected_load?: 'low' | 'medium' | 'high';
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/positions/${encodeURIComponent(positionId)}`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  delete(positionId: string): Promise<void> {
    return this.http.request<void>({
      path: `/positions/${encodeURIComponent(positionId)}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }

  applications(
    positionId: string,
    q: PositionApplicationsQuery = {},
  ): Promise<PageResult<ApplicationDTO>> {
    return this.http.request<PageResult<ApplicationDTO>>({
      path: `/positions/${encodeURIComponent(positionId)}/applications`,
      method: 'GET',
      query: q,
    });
  }

  apply(
    positionId: string,
    body: { message?: string | null } = {},
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/positions/${encodeURIComponent(positionId)}/applications`,
      method: 'POST',
      jsonBody: body,
    });
  }
}
