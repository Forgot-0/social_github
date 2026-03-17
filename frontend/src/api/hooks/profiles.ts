"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type {
  AddContactProfileRequest,
  AvatarPreSignUrlRequest,
  AvatarPresignResponse,
  AvatarUploadCompleteRequest,
  PageResult,
  PaginationParams,
  ProfileCreateRequest,
  ProfileDTO,
  ProfileUpdateRequest,
} from "@/types";

export const profileKeys = {
  all: ["profiles"] as const,
  list: (params?: PaginationParams) => [...profileKeys.all, "list", params] as const,
  detail: (id: number) => [...profileKeys.all, "detail", id] as const,
};

export function useProfilesQuery(params?: PaginationParams) {
  return useQuery({
    queryKey: profileKeys.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<PageResult<ProfileDTO>>("/v1/profiles/", { params });
      return data;
    },
  });
}

export function useProfileQuery(profileId: number) {
  return useQuery({
    queryKey: profileKeys.detail(profileId),
    queryFn: async () => {
      const { data } = await apiClient.get<ProfileDTO>(`/v1/profiles/${profileId}`);
      return data;
    },
    enabled: profileId > 0,
    retry: (failureCount, error) => {
      if (error && "response" in error && (error as { response?: { status?: number } }).response?.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useCreateProfileMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: ProfileCreateRequest) => {
      await apiClient.post("/v1/profiles/", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
  });
}

export function useUpdateProfileMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ profileId, body }: { profileId: number; body: ProfileUpdateRequest }) => {
      await apiClient.put(`/v1/profiles/${profileId}`, body);
    },
    onSuccess: (_data, { profileId }) => {
      queryClient.invalidateQueries({ queryKey: profileKeys.detail(profileId) });
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
  });
}

export function useAvatarPresignMutation() {
  return useMutation({
    mutationFn: async (body: AvatarPreSignUrlRequest) => {
      const { data } = await apiClient.post<AvatarPresignResponse>(
        "/v1/profiles/avatar/presign",
        body,
      );
      return data;
    },
  });
}

export function useAvatarUploadCompleteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: AvatarUploadCompleteRequest) => {
      await apiClient.post("/v1/profiles/avatar/upload_complete", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
  });
}

export function useAddContactMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      profileId,
      body,
    }: {
      profileId: number;
      body: AddContactProfileRequest;
    }) => {
      await apiClient.post(`/v1/profiles/${profileId}/contacts`, body);
    },
    onSuccess: (_data, { profileId }) => {
      queryClient.invalidateQueries({ queryKey: profileKeys.detail(profileId) });
    },
  });
}

export function useDeleteContactMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      profileId,
      providerContact,
    }: {
      profileId: number;
      providerContact: string;
    }) => {
      await apiClient.delete(`/v1/profiles/${profileId}/${providerContact}/delete`);
    },
    onSuccess: (_data, { profileId }) => {
      queryClient.invalidateQueries({ queryKey: profileKeys.detail(profileId) });
    },
  });
}
