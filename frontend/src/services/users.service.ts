import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  PageResult,
  SessionDTO,
  UserDTO,
  UserResponse,
} from '../domain/types/api.types';

export interface UsersListQuery {
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
  role_names?: readonly string[];
  permission_names?: readonly string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export class UsersService {
  constructor(private readonly http: IHttpClient) {}

  register(body: {
    username: string;
    email: string;
    password: string;
    repeat_password: string;
  }): Promise<UserResponse> {
    return this.http.request<UserResponse>({
      path: '/users/register',
      method: 'POST',
      jsonBody: body,
    });
  }

  me(): Promise<UserResponse> {
    return this.http.request<UserResponse>({
      path: '/users/me',
      method: 'GET',
    });
  }

  list(q: UsersListQuery = {}): Promise<PageResult<UserDTO>> {
    const { role_names, permission_names, page, page_size, sort, ...scalar } =
      q;
    return this.http.request<PageResult<UserDTO>>({
      path: '/users/',
      method: 'GET',
      query: {
        ...scalar,
        page,
        page_size,
        sort,
      },
      queryMulti: {
        role_names,
        permission_names,
      },
    });
  }

  mySessions(): Promise<SessionDTO[]> {
    return this.http.request<SessionDTO[]>({
      path: '/users/sessions',
      method: 'GET',
    });
  }

  assignRole(
    userId: number,
    role_name: string,
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/users/${userId}/roles`,
      method: 'POST',
      jsonBody: { role_name },
    });
  }

  removeRole(userId: number, roleName: string): Promise<void> {
    return this.http.request<void>({
      path: `/users/${userId}/roles/${encodeURIComponent(roleName)}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }

  addPermissions(
    userId: number,
    permissions: string[],
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/users/${userId}/permissions`,
      method: 'POST',
      jsonBody: { permissions },
    });
  }

  removePermissions(userId: number, permissions: string[]): Promise<void> {
    return this.http.request<void>({
      path: `/users/${userId}/permissions`,
      method: 'DELETE',
      jsonBody: { permissions },
      parseAs: 'void',
    });
  }
}
