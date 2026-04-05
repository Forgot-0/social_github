import type { PageResult } from '../../types/api/common.ts';
import type { ProjectRoleDTO } from '../../types/api/role.ts';
import { apiGet, type QueryParamValue } from '../api/client.ts';

export interface ListProjectRolesQuery {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listProjectRoles(
  query?: ListProjectRolesQuery,
): Promise<PageResult<ProjectRoleDTO>> {
  return apiGet<PageResult<ProjectRoleDTO>>('/project_roles/', {
    query: query as Record<string, QueryParamValue>,
  });
}
