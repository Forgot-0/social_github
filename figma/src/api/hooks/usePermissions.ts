/**
 * React Query hooks for Permissions
 */

import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { permissionsApi } from '../client';
import type {
  PermissionDTO,
  PermissionListParams,
  PermissionCreateRequest,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

// Query keys
export const permissionKeys = {
  all: ['permissions'] as const,
  list: (params?: PermissionListParams) =>
    [...permissionKeys.all, 'list', params] as const,
};

/**
 * Get permissions list query
 */
export const usePermissionsQuery = (
  params?: PermissionListParams,
  options?: Omit<
    UseQueryOptions<PageResult<PermissionDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: permissionKeys.list(params),
    queryFn: () => permissionsApi.getPermissions(params),
    ...options,
  });
};

/**
 * Create permission mutation
 */
export const useCreatePermissionMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, PermissionCreateRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: permissionsApi.createPermission,
    onSuccess: () => {
      // Invalidate permissions list
      queryClient.invalidateQueries({ queryKey: permissionKeys.all });
    },
    ...options,
  });
};

/**
 * Delete permission mutation
 */
export const useDeletePermissionMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: permissionsApi.deletePermission,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.all });
    },
    ...options,
  });
};
