import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { positionsApi } from '../client';
import type {
  PositionDTO,
  PositionListParams,
  PositionUpdateRequest,
  ApplicationDTO,
  ApplicationListParams,
  ApplicationCreateRequest,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const positionKeys = {
  all: ['positions'] as const,
  list: (params?: PositionListParams) => [...positionKeys.all, 'list', params] as const,
  detail: (id: string) => [...positionKeys.all, 'detail', id] as const,
  applications: (id: string, params?: ApplicationListParams) =>
    [...positionKeys.all, id, 'applications', params] as const,
};

export const usePositionsQuery = (
  params?: PositionListParams,
  options?: Omit<
    UseQueryOptions<PageResult<PositionDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: positionKeys.list(params),
    queryFn: () => positionsApi.getPositions(params),
    ...options,
  });
};

export const usePositionQuery = (
  positionId: string,
  options?: Omit<UseQueryOptions<PositionDTO, AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: positionKeys.detail(positionId),
    queryFn: () => positionsApi.getPosition(positionId),
    ...options,
  });
};

export const usePositionApplicationsQuery = (
  positionId: string,
  params?: ApplicationListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ApplicationDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: positionKeys.applications(positionId, params),
    queryFn: () => positionsApi.getApplications(positionId, params),
    ...options,
  });
};

export const useUpdatePositionMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { positionId: string; data: PositionUpdateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ positionId, data }) => positionsApi.updatePosition(positionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
    ...options,
  });
};

export const useDeletePositionMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: positionsApi.deletePosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
    ...options,
  });
};

export const useApplyToPositionMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { positionId: string; data: ApplicationCreateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ positionId, data }) => positionsApi.applyToPosition(positionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: positionKeys.all });
    },
    ...options,
  });
};
