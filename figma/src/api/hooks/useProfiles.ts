import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { profilesApi } from '../client';
import type {
  ProfileDTO,
  ProfileListParams,
  ProfileCreateRequest,
  ProfileUpdateRequest,
  AddContactProfileRequest,
  AvatarPreSignUrlRequest,
  AvatarPresignResponse,
  AvatarUploadCompleteRequest,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const profileKeys = {
  all: ['profiles'] as const,
  list: (params?: ProfileListParams) => [...profileKeys.all, 'list', params] as const,
  detail: (id: number) => [...profileKeys.all, 'detail', id] as const,
};

export const useProfilesQuery = (
  params?: ProfileListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ProfileDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: profileKeys.list(params),
    queryFn: () => profilesApi.getProfiles(params),
    ...options,
  });
};

export const useProfileQuery = (
  profileId: number,
  options?: Omit<UseQueryOptions<ProfileDTO, AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: profileKeys.detail(profileId),
    queryFn: () => profilesApi.getProfile(profileId),
    ...options,
  });
};

export const useCreateProfileMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, ProfileCreateRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profilesApi.createProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    ...options,
  });
};

export const useUpdateProfileMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { profileId: number; data: ProfileUpdateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ profileId, data }) => profilesApi.updateProfile(profileId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    ...options,
  });
};

export const useGetAvatarPresignUrlMutation = (
  options?: UseMutationOptions<AvatarPresignResponse, AxiosError<ApiError>, AvatarPreSignUrlRequest>
) => {
  return useMutation({
    mutationFn: profilesApi.getAvatarPresignUrl,
    ...options,
  });
};

export const useUploadAvatarCompleteMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, AvatarUploadCompleteRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profilesApi.uploadAvatarComplete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    ...options,
  });
};

export const useAddContactMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { profileId: number; data: AddContactProfileRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ profileId, data }) => profilesApi.addContact(profileId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    ...options,
  });
};

export const useRemoveContactMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { profileId: number; provideContact: string }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ profileId, provideContact }) =>
      profilesApi.removeContact(profileId, provideContact),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.all });
    },
    ...options,
  });
};
