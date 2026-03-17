"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  PageResult,
  PaginationParams,
  RoleCreateRequest,
  RoleDTO,
  RolePermissionRequest,
} from "@/types";

export const roleKeys = {
  all: ["roles"] as const,
  list: (params?: PaginationParams) => [...roleKeys.all, "list", params] as const,
};

export function useRolesQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: roleKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<RoleDTO>>("/v1/roles/", { params });
      return data;
    },
  });
}

export function useCreateRoleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: RoleCreateRequest) => {
      await apiClient.post("/v1/roles/", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
  });
}

export function useAddRolePermissionsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ roleName, body }: { roleName: string; body: RolePermissionRequest }) => {
      await apiClient.post(`/v1/roles/${roleName}/permissions`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
  });
}

export function useRemoveRolePermissionsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ roleName, body }: { roleName: string; body: RolePermissionRequest }) => {
      await apiClient.delete(`/v1/roles/${roleName}/permissions`, { data: body });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.all });
    },
  });
}
