import type { ProjectRoleDTO } from './role.ts';

export interface MemberDTO {
  id: number;
  project_id: number;
  user_id: number;
  role_id: number | null;
  status: string;
  invited_by: number | null;
  joined_at: string | null;
  permissions_overrides: Record<string, unknown>;
  role: ProjectRoleDTO | null;
  project: ProjectDTO | null;
}

export interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: 'public' | 'private';
  meta_data: Record<string, unknown>;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  memberships: MemberDTO[];
}
