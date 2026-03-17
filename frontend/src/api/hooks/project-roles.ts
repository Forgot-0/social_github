"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { PageResult, PaginationParams, ProjectRoleDTO } from "@/types";

export const projectRoleKeys = {
  all: ["project_roles"] as const,
  list: (params?: PaginationParams) => [...projectRoleKeys.all, "list", params] as const,
};

export function useProjectRolesQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: projectRoleKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<ProjectRoleDTO>>("/v1/project_roles/", { params });
      return data;
    },
  });
}

