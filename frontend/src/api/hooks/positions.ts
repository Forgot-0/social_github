"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  PageResult,
  PaginationParams,
  PositionCreateRequest,
  PositionDTO,
  PositionUpdateRequest,
} from "@/types";

export const positionKeys = {
  all: ["positions"] as const,
  list: (params?: PaginationParams) => [...positionKeys.all, "list", params] as const,
  detail: (id: string) => [...positionKeys.all, "detail", id] as const,
};

export function usePositionsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: positionKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<PositionDTO>>("/v1/positions/", { params });
      return data;
    },
  });
}

export function usePositionQuery(positionId: string) {
  return useQuery({
    queryKey: positionKeys.detail(positionId),
    queryFn: async () => {
      const { data } = await apiClient.get<PositionDTO>(`/v1/positions/${positionId}`);
      return data;
    },
    enabled: !!positionId,
  });
}

export function useCreatePositionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      body,
    }: {
      projectId: number;
      body: PositionCreateRequest;
    }) => {
      await apiClient.post(`/v1/projects/${projectId}/positions`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
  });
}

export function useUpdatePositionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      positionId,
      body,
    }: {
      positionId: string;
      body: PositionUpdateRequest;
    }) => {
      await apiClient.put(`/v1/positions/${positionId}`, body);
    },
    onSuccess: (_data, { positionId }) => {
      queryClient.invalidateQueries({ queryKey: positionKeys.detail(positionId) });
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
  });
}

export function useDeletePositionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ positionId }: { positionId: string }) => {
      await apiClient.delete(`/v1/positions/${positionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
  });
}
