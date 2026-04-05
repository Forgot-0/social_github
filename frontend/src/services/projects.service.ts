import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  MemberDTO,
  PageResult,
  PositionDTO,
  ProjectDTO,
} from '../domain/types/api.types';

export interface ProjectsListQuery {
  name?: string;
  slug?: string;
  tags?: readonly string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface ProjectPositionsQuery {
  title?: string;
  required_skills?: readonly string[];
  is_open?: boolean;
  location_type?: 'remote' | 'onsite' | 'hybrid';
  expected_load?: 'low' | 'medium' | 'high';
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface MyProjectsQuery {
  page?: number;
  page_size?: number;
}

export class ProjectsService {
  constructor(private readonly http: IHttpClient) {}

  create(body: {
    name: string;
    slug: string;
    small_description?: string | null;
    description?: string | null;
    visibility?: 'public' | 'private';
    tags?: string[];
    meta_data?: Record<string, unknown>;
  }): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: '/projects/',
      method: 'POST',
      jsonBody: body,
    });
  }

  list(q: ProjectsListQuery = {}): Promise<PageResult<ProjectDTO>> {
    const { tags, page, page_size, sort, ...rest } = q;
    return this.http.request<PageResult<ProjectDTO>>({
      path: '/projects/',
      method: 'GET',
      query: { ...rest, page, page_size, sort },
      queryMulti: { tags },
    });
  }

  my(q: MyProjectsQuery = {}): Promise<PageResult<ProjectDTO>> {
    return this.http.request<PageResult<ProjectDTO>>({
      path: '/projects/my',
      method: 'GET',
      query: q,
    });
  }

  get(projectId: number): Promise<ProjectDTO> {
    return this.http.request<ProjectDTO>({
      path: `/projects/${projectId}`,
      method: 'GET',
    });
  }

  update(
    projectId: number,
    body: {
      name?: string;
      description?: string | null;
      visibility?: 'public' | 'private';
      tags?: string[];
      meta_data?: Record<string, unknown>;
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/projects/${projectId}`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  delete(projectId: number): Promise<void> {
    return this.http.request<void>({
      path: `/projects/${projectId}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }

  positions(
    projectId: number,
    q: ProjectPositionsQuery = {},
  ): Promise<PageResult<PositionDTO>> {
    const { required_skills, page, page_size, sort, ...rest } = q;
    return this.http.request<PageResult<PositionDTO>>({
      path: `/projects/${projectId}/positions`,
      method: 'GET',
      query: { ...rest, page, page_size, sort },
      queryMulti: { required_skills },
    });
  }

  createPosition(
    projectId: number,
    body: {
      title: string;
      description: string;
      responsibilities?: string | null;
      required_skills?: string[];
      location_type?: 'remote' | 'onsite' | 'hybrid';
      expected_load?: 'low' | 'medium' | 'high';
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/projects/${projectId}/positions`,
      method: 'POST',
      jsonBody: body,
    });
  }

  invite(
    projectId: number,
    body: {
      user_id: number;
      role_id: number;
      permissions_overrides?: Record<string, unknown>;
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/projects/${projectId}/invite`,
      method: 'POST',
      jsonBody: body,
    });
  }

  acceptMembership(projectId: number): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/projects/${projectId}/members/accept`,
      method: 'POST',
    });
  }

  updateMemberPermissions(
    projectId: number,
    userId: number,
    body: { permissions_overrides: Record<string, unknown> },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/projects/${projectId}/members/${userId}/permissions`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  myInvites(
    q: { page?: number; page_size?: number } = {},
  ): Promise<PageResult<MemberDTO>> {
    return this.http.request<PageResult<MemberDTO>>({
      path: '/projects/invites/my',
      method: 'GET',
      query: q,
    });
  }
}
