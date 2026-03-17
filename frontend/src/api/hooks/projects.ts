"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  InviteMemberRequest,
  MemberUpdatePermissionsRequest,
  PageResult,
  PaginationParams,
  ProjectCreateRequest,
  ProjectDTO,
  ProjectUpdateRequest,
} from "@/types";

export const projectKeys = {
  all: ["projects"] as const,
  list: (params?: PaginationParams) => [...projectKeys.all, "list", params] as const,
  my: (params?: PaginationParams) => [...projectKeys.all, "my", params] as const,
  detail: (id: number) => [...projectKeys.all, "detail", id] as const,
};

export function useProjectsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<ProjectDTO>>("/v1/projects/", { params });
      return data;
    },
  });
}

export function useMyProjectsQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: projectKeys.my(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<ProjectDTO>>("/v1/projects/my", { params });
      return data;
    },
  });
}

export function useProjectQuery(projectId: number) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: async () => {
      const { data } = await apiClient.get<ProjectDTO>(`/v1/projects/${projectId}`);
      return data;
    },
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: ProjectCreateRequest) => {
      await apiClient.post("/v1/projects/", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

export function useUpdateProjectMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      body,
    }: {
      projectId: number;
      body: ProjectUpdateRequest;
    }) => {
      await apiClient.put(`/v1/projects/${projectId}`, body);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useInviteMemberMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      body,
    }: {
      projectId: number;
      body: InviteMemberRequest;
    }) => {
      await apiClient.post(`/v1/projects/${projectId}/invite`, body);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useAcceptInviteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ projectId }: { projectId: number }) => {
      await apiClient.post(`/v1/projects/${projectId}/members/accept`);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useUpdateMemberPermissionsMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      userId,
      body,
    }: {
      projectId: number;
      userId: number;
      body: MemberUpdatePermissionsRequest;
    }) => {
      await apiClient.put(`/v1/projects/${projectId}/members/${userId}/permissions`, body);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}
