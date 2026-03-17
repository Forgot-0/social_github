"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  PageResult,
  PaginationParams,
  RoleAssignRequest,
  UserCreateRequest,
  UserDTO,
  UserPermissionRequest,
  UserResponse,
} from "@/types";

export const userKeys = {
  all: ["users"] as const,
  list: (params?: PaginationParams) => [...userKeys.all, "list", params] as const,
  me: () => ["currentUser"] as const,
};

export function useCurrentUserQuery(enabled = true) {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: async () => {
      const { data } = await apiClient.get<UserResponse>("/v1/users/me");
      return data;
    },
    enabled,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useUsersQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<UserDTO>>("/v1/users/", { params });
      return data;
    },
  });
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: async (body: UserCreateRequest) => {
      const { data } = await apiClient.post<UserResponse>("/v1/users/register", body);
      return data;
    },
  });
}

export function useAssignRoleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, body }: { userId: number; body: RoleAssignRequest }) => {
      await apiClient.post(`/v1/users/${userId}/roles`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useRemoveRoleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, roleName }: { userId: number; roleName: string }) => {
      await apiClient.delete(`/v1/users/${userId}/roles/${roleName}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useAssignUserPermissionsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, body }: { userId: number; body: UserPermissionRequest }) => {
      await apiClient.post(`/v1/users/${userId}/permissions`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}

export function useRemoveUserPermissionsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, body }: { userId: number; body: UserPermissionRequest }) => {
      await apiClient.delete(`/v1/users/${userId}/permissions`, { data: body });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
}
