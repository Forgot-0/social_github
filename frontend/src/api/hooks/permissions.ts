"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { PageResult, PaginationParams, PermissionCreateRequest, PermissionDTO } from "@/types";

export const permissionKeys = {
  all: ["permissions"] as const,
  list: (params?: PaginationParams) => [...permissionKeys.all, "list", params] as const,
};

export function usePermissionsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: permissionKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<PermissionDTO>>("/v1/permissions/", {
        params,
      });
      return data;
    },
  });
}

export function useCreatePermissionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: PermissionCreateRequest) => {
      await apiClient.post("/v1/permissions/", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.all });
    },
  });
}

export function useDeletePermissionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name }: { name: string }) => {
      await apiClient.delete(`/v1/permissions/${name}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.all });
    },
  });
}
