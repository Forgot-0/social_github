"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { PageResult, PaginationParams, SessionDTO } from "@/types";

export const sessionKeys = {
  all: ["sessions"] as const,
  list: (params?: PaginationParams) => [...sessionKeys.all, "list", params] as const,
  userSessions: () => ["userSessions"] as const,
};

export function useSessionsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: sessionKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<SessionDTO>>("/v1/sessions/", { params });
      return data;
    },
  });
}

export function useUserSessionsQuery() {
  return useQuery({
    queryKey: sessionKeys.userSessions(),
    queryFn: async () => {
      const { data } = await apiClient.get<SessionDTO[]>("/v1/users/sessions");
      return data;
    },
  });
}

export function useDeleteSessionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sessionId }: { sessionId: number }) => {
      await apiClient.delete(`/v1/sessions/${sessionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.all });
      queryClient.invalidateQueries({ queryKey: sessionKeys.userSessions() });
    },
  });
}
