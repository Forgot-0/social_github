"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  ApplicationCreateRequest,
  ApplicationDTO,
  PageResult,
  PaginationParams,
} from "@/types";

export const applicationKeys = {
  all: ["applications"] as const,
  list: (params?: PaginationParams) => [...applicationKeys.all, "list", params] as const,
};

export function useApplicationsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: applicationKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<ApplicationDTO>>("/v1/applications/", {
        params,
      });
      return data;
    },
  });
}

export function useApplyToPositionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      positionId,
      body,
    }: {
      positionId: string;
      body: ApplicationCreateRequest;
    }) => {
      await apiClient.post(`/v1/positions/${positionId}/apply`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
  });
}

export function useApproveApplicationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ applicationId }: { applicationId: string }) => {
      await apiClient.post(`/v1/applications/${applicationId}/approve`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
  });
}

export function useRejectApplicationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ applicationId }: { applicationId: string }) => {
      await apiClient.post(`/v1/applications/${applicationId}/reject`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
  });
}
