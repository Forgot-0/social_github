import type { PageResult } from '../../types/api/common.ts';
import type { MemberDTO, ProjectDTO } from '../../types/api/project.ts';
import type { PositionDTO } from '../../types/api/position.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  type QueryParamValue,
} from '../api/client.ts';

export interface CreateProjectBody {
  name: string;
  slug: string;
  small_description?: string | null;
  description?: string | null;
  visibility?: 'public' | 'private';
  tags?: string[];
  meta_data?: Record<string, unknown>;
}

export async function createProject(body: CreateProjectBody): Promise<void> {
  await apiPost<unknown>('/projects/', { body });
}

export interface ListProjectsQuery {
  name?: string;
  slug?: string;
  tags?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listProjects(
  query?: ListProjectsQuery,
): Promise<PageResult<ProjectDTO>> {
  return apiGet<PageResult<ProjectDTO>>('/projects/', {
    query: query as Record<string, QueryParamValue>,
  });
}

export interface ListMyProjectsQuery {
  page?: number;
  page_size?: number;
}

export async function listMyProjects(
  query?: ListMyProjectsQuery,
): Promise<PageResult<ProjectDTO>> {
  return apiGet<PageResult<ProjectDTO>>('/projects/my', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function getProject(projectId: number): Promise<ProjectDTO> {
  return apiGet<ProjectDTO>(`/projects/${projectId}`);
}

export interface UpdateProjectBody {
  name?: string;
  description?: string | null;
  visibility?: 'public' | 'private';
  tags?: string[];
  meta_data?: Record<string, unknown>;
}

export async function updateProject(
  projectId: number,
  body: UpdateProjectBody,
): Promise<void> {
  await apiPut<unknown>(`/projects/${projectId}`, { body });
}

export async function deleteProject(projectId: number): Promise<void> {
  await apiDelete(`/projects/${projectId}`);
}

export interface ListProjectPositionsQuery {
  title?: string;
  required_skills?: string[];
  is_open?: boolean;
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listProjectPositions(
  projectId: number,
  query?: ListProjectPositionsQuery,
): Promise<PageResult<PositionDTO>> {
  return apiGet<PageResult<PositionDTO>>(`/projects/${projectId}/positions`, {
    query: query as Record<string, QueryParamValue>,
  });
}

export interface CreatePositionBody {
  title: string;
  description: string;
  responsibilities?: string | null;
  required_skills?: string[];
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
}

export async function createProjectPosition(
  projectId: number,
  body: CreatePositionBody,
): Promise<void> {
  await apiPost<unknown>(`/projects/${projectId}/positions`, { body });
}

export interface InviteMemberBody {
  user_id: number;
  role_id: number;
  permissions_overrides?: Record<string, unknown>;
}

export async function inviteProjectMember(
  projectId: number,
  body: InviteMemberBody,
): Promise<void> {
  await apiPost<unknown>(`/projects/${projectId}/invite`, { body });
}

export async function acceptProjectInvite(projectId: number): Promise<void> {
  await apiPost<unknown>(`/projects/${projectId}/members/accept`, { body: {} });
}

export interface UpdateMemberPermissionsBody {
  permissions_overrides: Record<string, unknown>;
}

export async function updateProjectMemberPermissions(
  projectId: number,
  userId: number,
  body: UpdateMemberPermissionsBody,
): Promise<void> {
  await apiPut<unknown>(
    `/projects/${projectId}/members/${userId}/permissions`,
    { body },
  );
}

export async function listMyProjectInvites(): Promise<PageResult<MemberDTO>> {
  return apiGet<PageResult<MemberDTO>>('/projects/invites/my');
}
