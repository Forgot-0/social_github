/**
 * React Query hooks for Users
 */

import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { usersApi } from '../client';
import type {
  UserResponse,
  UserDTO,
  UserCreateRequest,
  UserListParams,
  PageResult,
  RoleAssignRequest,
  UserPermissionRequest,
  SessionDTO,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

// Query keys
export const userKeys = {
  all: ['users'] as const,
  me: () => [...userKeys.all, 'me'] as const,
  list: (params?: UserListParams) => [...userKeys.all, 'list', params] as const,
  sessions: () => [...userKeys.all, 'sessions'] as const,
};

/**
 * Get current user query
 */
export const useMeQuery = (
  options?: Omit<UseQueryOptions<UserResponse, AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: usersApi.getMe,
    ...options,
  });
};

/**
 * Get users list query
 */
export const useUsersQuery = (
  params?: UserListParams,
  options?: Omit<
    UseQueryOptions<PageResult<UserDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => usersApi.getUsers(params),
    ...options,
  });
};

/**
 * Get user sessions query
 */
export const useSessionsQuery = (
  options?: Omit<
    UseQueryOptions<SessionDTO[], AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: userKeys.sessions(),
    queryFn: usersApi.getSessions,
    ...options,
  });
};

/**
 * Register user mutation
 */
export const useRegisterMutation = (
  options?: UseMutationOptions<UserResponse, AxiosError<ApiError>, UserCreateRequest>
) => {
  return useMutation({
    mutationFn: usersApi.register,
    ...options,
  });
};

/**
 * Assign role mutation
 */
export const useAssignRoleMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { userId: number; data: RoleAssignRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }) => usersApi.assignRole(userId, data),
    onSuccess: () => {
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
    ...options,
  });
};

/**
 * Remove role mutation
 */
export const useRemoveRoleMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { userId: number; roleName: string }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleName }) => usersApi.removeRole(userId, roleName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
    ...options,
  });
};

/**
 * Add permissions mutation
 */
export const useAddPermissionsMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { userId: number; data: UserPermissionRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }) => usersApi.addPermissions(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
    ...options,
  });
};

/**
 * Remove permissions mutation
 */
export const useRemovePermissionsMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { userId: number; data: UserPermissionRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }) => usersApi.removePermissions(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
    ...options,
  });
};
