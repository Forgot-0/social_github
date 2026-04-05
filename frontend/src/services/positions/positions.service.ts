import type { PageResult } from '../../types/api/common.ts';
import type { ApplicationDTO } from '../../types/api/application.ts';
import type { PositionDTO } from '../../types/api/position.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  type QueryParamValue,
} from '../api/client.ts';

export interface ListPositionsQuery {
  project_id?: number;
  title?: string;
  required_skills?: string[];
  is_open?: boolean;
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listPositions(
  query?: ListPositionsQuery,
): Promise<PageResult<PositionDTO>> {
  return apiGet<PageResult<PositionDTO>>('/positions/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function getPosition(positionId: string): Promise<PositionDTO> {
  return apiGet<PositionDTO>(`/positions/${encodeURIComponent(positionId)}`);
}

export interface UpdatePositionBody {
  title?: string;
  description?: string;
  responsibilities?: string | null;
  required_skills?: string[];
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
}

export async function updatePosition(
  positionId: string,
  body: UpdatePositionBody,
): Promise<void> {
  await apiPut<unknown>(`/positions/${encodeURIComponent(positionId)}`, {
    body,
  });
}

export async function deletePosition(positionId: string): Promise<void> {
  await apiDelete(`/positions/${encodeURIComponent(positionId)}`);
}

export interface ListPositionApplicationsQuery {
  project_id?: number;
  candidate_id?: number;
  status?: 'pending' | 'accepted' | 'rejected';
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listPositionApplications(
  positionId: string,
  query?: ListPositionApplicationsQuery,
): Promise<PageResult<ApplicationDTO>> {
  return apiGet<PageResult<ApplicationDTO>>(
    `/positions/${encodeURIComponent(positionId)}/applications`,
    {
      query: query as Record<string, QueryParamValue>,
    },
  );
}

export interface ApplyToPositionBody {
  message?: string | null;
}

export async function applyToPosition(
  positionId: string,
  body: ApplyToPositionBody = {},
): Promise<void> {
  await apiPost<unknown>(
    `/positions/${encodeURIComponent(positionId)}/applications`,
    { body },
  );
}
