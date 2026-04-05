import type { PageResult } from '../../types/api/common.ts';
import type { RoleDTO } from '../../types/api/role.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  type QueryParamValue,
} from '../api/client.ts';

export interface CreateRoleBody {
  name: string;
  description: string;
  security_level: number;
  permissions?: string[];
}

export async function createRole(body: CreateRoleBody): Promise<void> {
  await apiPost<unknown>('/roles/', { body });
}

export interface ListRolesQuery {
  name?: string;
  security_level?: number;
  min_security_level?: number;
  max_security_level?: number;
  permission_names?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listRoles(
  query?: ListRolesQuery,
): Promise<PageResult<RoleDTO>> {
  return apiGet<PageResult<RoleDTO>>('/roles/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function addRolePermissions(
  roleName: string,
  permissions: string[],
): Promise<void> {
  await apiPost<unknown>(`/roles/${encodeURIComponent(roleName)}/permissions`, {
    body: { permissions },
  });
}

export async function removeRolePermissions(
  roleName: string,
  permissions: string[],
): Promise<void> {
  await apiDelete(`/roles/${encodeURIComponent(roleName)}/permissions`, {
    body: { permissions },
  });
}
