import type { PageResult } from '../../types/api/common.ts';
import type { UserDTO, UserResponse } from '../../types/api/user.ts';
import type { SessionDTO } from '../../types/api/session.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  type QueryParamValue,
} from '../api/client.ts';

export interface RegisterUserBody {
  username: string;
  email: string;
  password: string;
  repeat_password: string;
}

export async function registerUser(
  body: RegisterUserBody,
): Promise<UserResponse> {
  return apiPost<UserResponse>('/users/register', { body, auth: false });
}

export async function getCurrentUser(): Promise<UserResponse> {
  return apiGet<UserResponse>('/users/me');
}

export interface ListUsersQuery {
  email?: string;
  username?: string;
  is_active?: boolean;
  is_verified?: boolean;
  is_deleted?: boolean;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
  has_oauth_accounts?: boolean;
  has_sessions?: boolean;
  role_names?: string[];
  permission_names?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listUsers(
  query?: ListUsersQuery,
): Promise<PageResult<UserDTO>> {
  return apiGet<PageResult<UserDTO>>('/users/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function listMySessions(): Promise<SessionDTO[]> {
  return apiGet<SessionDTO[]>('/users/sessions');
}

export async function assignUserRole(
  userId: number,
  roleName: string,
): Promise<void> {
  await apiPost<unknown>(`/users/${userId}/roles`, {
    body: { role_name: roleName },
  });
}

export async function removeUserRole(
  userId: number,
  roleName: string,
): Promise<void> {
  await apiDelete(`/users/${userId}/roles/${encodeURIComponent(roleName)}`);
}

export async function addUserPermissions(
  userId: number,
  permissions: string[],
): Promise<void> {
  await apiPost<unknown>(`/users/${userId}/permissions`, {
    body: { permissions },
  });
}

export async function removeUserPermissions(
  userId: number,
  permissions: string[],
): Promise<void> {
  await apiDelete(`/users/${userId}/permissions`, { body: { permissions } });
}
