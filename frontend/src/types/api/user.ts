import type { PermissionDTO, RoleDTO } from './role.ts';
import type { SessionDTO } from './session.ts';

export interface UserResponse {
  id: number;
  username: string;
  email: string;
}

export interface UserDTO {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  roles: RoleDTO[];
  permissions: PermissionDTO[];
  sessions: SessionDTO[];
}
