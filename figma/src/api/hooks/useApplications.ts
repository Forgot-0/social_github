import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { applicationsApi } from '../client';
import type {
  ApplicationDTO,
  ApplicationListParams,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const applicationKeys = {
  all: ['applications'] as const,
  list: (params?: ApplicationListParams) => [...applicationKeys.all, 'list', params] as const,
  my: (params?: ApplicationListParams) => [...applicationKeys.all, 'my', params] as const,
};

export const useApplicationsQuery = (
  params?: ApplicationListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ApplicationDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: applicationKeys.list(params),
    queryFn: () => applicationsApi.getApplications(params),
    ...options,
  });
};

export const useMyApplicationsQuery = (
  params?: ApplicationListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ApplicationDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: applicationKeys.my(params),
    queryFn: () => applicationsApi.getMyApplications(params),
    ...options,
  });
};

export const useApproveApplicationMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: applicationsApi.approveApplication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
    ...options,
  });
};

export const useRejectApplicationMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: applicationsApi.rejectApplication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
    ...options,
  });
};

export const useCreateApplicationMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { positionId: string; data?: { message?: string } }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ positionId, data }) => applicationsApi.createApplication(positionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: applicationKeys.all });
    },
    ...options,
  });
};