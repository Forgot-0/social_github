import type { PageResult } from '../../types/api/common.ts';
import type { PermissionDTO } from '../../types/api/role.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  type QueryParamValue,
} from '../api/client.ts';

export async function createPermission(name: string): Promise<void> {
  await apiPost<unknown>('/permissions/', { body: { name } });
}

export interface ListPermissionsQuery {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listPermissions(
  query?: ListPermissionsQuery,
): Promise<PageResult<PermissionDTO>> {
  return apiGet<PageResult<PermissionDTO>>('/permissions/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function deletePermission(name: string): Promise<void> {
  await apiDelete(`/permissions/${encodeURIComponent(name)}`);
}
