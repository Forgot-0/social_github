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
