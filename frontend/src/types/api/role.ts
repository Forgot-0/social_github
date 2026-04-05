export interface PermissionDTO {
  id: number;
  name: string;
}

export interface RoleDTO {
  id: number;
  name: string;
  description: string;
  security_level: number;
  permissions: PermissionDTO[];
}

export interface ProjectRoleDTO {
  id: number;
  name: string;
  permissions: Record<string, unknown>;
}
