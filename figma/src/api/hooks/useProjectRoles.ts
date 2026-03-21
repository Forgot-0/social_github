import {
  useQuery,
  UseQueryOptions,
} from '@tanstack/react-query';
import { projectRolesApi } from '../client';
import type {
  ProjectRoleDTO,
  ProjectRoleListParams,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const projectRoleKeys = {
  all: ['projectRoles'] as const,
  list: (params?: ProjectRoleListParams) => [...projectRoleKeys.all, 'list', params] as const,
  detail: (id: number) => [...projectRoleKeys.all, 'detail', id] as const,
};

export const useProjectRolesQuery = (
  params?: ProjectRoleListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ProjectRoleDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: projectRoleKeys.list(params),
    queryFn: () => projectRolesApi.getProjectRoles(params),
    ...options,
  });
};

export const useProjectRoleQuery = (
  roleId: number | null | undefined,
  options?: Omit<
    UseQueryOptions<ProjectRoleDTO | null, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: projectRoleKeys.detail(roleId || 0),
    queryFn: async () => {
      if (!roleId) return null;
      // Load all roles and find the one we need
      const result = await projectRolesApi.getProjectRoles();
      const role = result.items.find(r => r.id === roleId);
      return role || null;
    },
    enabled: !!roleId,
    ...options,
  });
};