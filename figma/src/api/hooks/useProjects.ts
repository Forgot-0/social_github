import {
  useQuery,
  useMutation,
  UseQueryOptions,
  UseMutationOptions,
  useQueryClient,
} from '@tanstack/react-query';
import { projectsApi } from '../client';
import type {
  ProjectDTO,
  ProjectListParams,
  ProjectCreateRequest,
  ProjectUpdateRequest,
  InviteMemberRequest,
  MemberUpdatePermissionsRequest,
  PositionListParams,
  PositionCreateRequest,
  PositionDTO,
  PageResult,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

export const projectKeys = {
  all: ['projects'] as const,
  list: (params?: ProjectListParams) => [...projectKeys.all, 'list', params] as const,
  my: (page?: number, pageSize?: number) => [...projectKeys.all, 'my', page, pageSize] as const,
  detail: (id: number) => [...projectKeys.all, 'detail', id] as const,
  positions: (id: number, params?: PositionListParams) =>
    [...projectKeys.all, id, 'positions', params] as const,
};

export const useProjectsQuery = (
  params?: ProjectListParams,
  options?: Omit<
    UseQueryOptions<PageResult<ProjectDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectsApi.getProjects(params),
    ...options,
  });
};

export const useMyProjectsQuery = (
  page?: number,
  pageSize?: number,
  options?: Omit<
    UseQueryOptions<PageResult<ProjectDTO>, AxiosError<ApiError>>,
    'queryKey' | 'queryFn'
  >
) => {
  return useQuery({
    queryKey: projectKeys.my(page, pageSize),
    queryFn: () => projectsApi.getMyProjects(page, pageSize),
    ...options,
  });
};

export const useProjectQuery = (
  projectId: number,
  options?: Omit<UseQueryOptions<ProjectDTO, AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectsApi.getProject(projectId),
    ...options,
  });
};

export const useProjectPositionsQuery = (
  projectId: number,
  params?: PositionListParams,
  options?: Omit<UseQueryOptions<PositionDTO[], AxiosError<ApiError>>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: projectKeys.positions(projectId, params),
    queryFn: () => projectsApi.getProjectPositions(projectId, params),
    ...options,
  });
};

export const useCreateProjectMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, ProjectCreateRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: projectsApi.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useUpdateProjectMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { projectId: number; data: ProjectUpdateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }) => projectsApi.updateProject(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useDeleteProjectMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, number>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: projectsApi.deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useCreatePositionMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { projectId: number; data: PositionCreateRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }) => projectsApi.createPosition(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useInviteMemberMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { projectId: number; data: InviteMemberRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, data }) => projectsApi.inviteMember(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useAcceptInviteMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, number>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: projectsApi.acceptInvite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};

export const useUpdateMemberPermissionsMutation = (
  options?: UseMutationOptions<
    void,
    AxiosError<ApiError>,
    { projectId: number; userId: number; data: MemberUpdatePermissionsRequest }
  >
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, userId, data }) =>
      projectsApi.updateMemberPermissions(projectId, userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
    ...options,
  });
};