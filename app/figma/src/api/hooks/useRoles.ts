import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { rolesApi } from '../client';
import type {
  RoleDTO,
  RoleListParams,
  RoleCreateRequest,
  RolePermissionRequest,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const roleKeys = {
  all: ['roles'] as const,
  list: (params?: RoleListParams) => [...roleKeys.all, 'list', params] as const,
};

export const useRolesQuery = (
  params?: RoleListParams,
  options?: Omit<
    UseQueryOptions<PageResult<RoleDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: roleKeys.list(params),
    queryFn: () => rolesApi.getRoles(params),
    ...options,
  });
};

export const useCreateRoleMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, RoleCreateRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rolesApi.createRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
    ...options,
  });
};

export const useAddRolePermissionsMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { roleName: string; data: RolePermissionRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ roleName, data }) => rolesApi.addPermissions(roleName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
    ...options,
  });
};

export const useRemoveRolePermissionsMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { roleName: string; data: RolePermissionRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ roleName, data }) => rolesApi.removePermissions(roleName, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
    ...options,
  });
};
