import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  PageResult,
  PermissionDTO,
  ProjectRoleDTO,
  RoleDTO,
} from '../domain/types/api.types';

export interface RolesListQuery {
  name?: string;
  security_level?: number;
  min_security_level?: number;
  max_security_level?: number;
  permission_names?: readonly string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface ProjectRolesListQuery {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface PermissionsListQuery {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export class RolesService {
  constructor(private readonly http: IHttpClient) {}

  createRole(body: {
    name: string;
    description: string;
    security_level: number;
    permissions?: string[];
  }): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: '/roles/',
      method: 'POST',
      jsonBody: body,
    });
  }

  listRoles(q: RolesListQuery = {}): Promise<PageResult<RoleDTO>> {
    const { permission_names, page, page_size, sort, ...rest } = q;
    return this.http.request<PageResult<RoleDTO>>({
      path: '/roles/',
      method: 'GET',
      query: { ...rest, page, page_size, sort },
      queryMulti: { permission_names },
    });
  }

  addRolePermissions(
    roleName: string,
    body: { permissions: string[] },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/roles/${encodeURIComponent(roleName)}/permissions`,
      method: 'POST',
      jsonBody: body,
    });
  }

  removeRolePermissions(
    roleName: string,
    body: { permissions: string[] },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/roles/${encodeURIComponent(roleName)}/permissions`,
      method: 'DELETE',
      jsonBody: body,
    });
  }

  listProjectRoles(
    q: ProjectRolesListQuery = {},
  ): Promise<PageResult<ProjectRoleDTO>> {
    return this.http.request<PageResult<ProjectRoleDTO>>({
      path: '/project_roles/',
      method: 'GET',
      query: q,
    });
  }

  createPermission(body: { name: string }): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: '/permissions/',
      method: 'POST',
      jsonBody: body,
    });
  }

  listPermissions(
    q: PermissionsListQuery = {},
  ): Promise<PageResult<PermissionDTO>> {
    return this.http.request<PageResult<PermissionDTO>>({
      path: '/permissions/',
      method: 'GET',
      query: q,
    });
  }

  deletePermission(name: string): Promise<void> {
    return this.http.request<void>({
      path: `/permissions/${encodeURIComponent(name)}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }
}
