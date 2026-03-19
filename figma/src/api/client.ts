import { axiosInstance, formatQueryParams } from './axiosInstance';
import type {
  AccessTokenResponse,
  LoginRequest,
  UserCreateRequest,
  UserResponse,
  UserDTO,
  UserListParams,
  PageResult,
  SendVerifyCodeRequest,
  VerifyEmailRequest,
  SendResetPasswordCodeRequest,
  ResetPasswordRequest,
  OAuthUrlResponse,
  PermissionDTO,
  PermissionListParams,
  PermissionCreateRequest,
  RoleAssignRequest,
  UserPermissionRequest,
  SessionDTO,
  RoleDTO,
  RoleCreateRequest,
  RoleListParams,
  RolePermissionRequest,
  SessionListParams,
  ProfileDTO,
  ProfileCreateRequest,
  ProfileUpdateRequest,
  ProfileListParams,
  AddContactProfileRequest,
  AvatarPreSignUrlRequest,
  AvatarPresignResponse,
  AvatarUploadCompleteRequest,
  ProjectDTO,
  ProjectCreateRequest,
  ProjectUpdateRequest,
  ProjectListParams,
  InviteMemberRequest,
  MemberUpdatePermissionsRequest,
  PositionDTO,
  PositionCreateRequest,
  PositionUpdateRequest,
  PositionListParams,
  ApplicationDTO,
  ApplicationCreateRequest,
  ApplicationListParams,
  ProjectRoleDTO,
  ProjectRoleListParams,
} from './types';

export const authApi = {
  async login(data: LoginRequest): Promise<AccessTokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await axiosInstance.post<AccessTokenResponse>(
      '/api/v1/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  },

  async refresh(): Promise<AccessTokenResponse> {
    const response = await axiosInstance.post<AccessTokenResponse>(
      '/api/v1/auth/refresh'
    );
    return response.data;
  },

  async logout(): Promise<void> {
    await axiosInstance.post('/api/v1/auth/logout');
  },

  async sendVerificationCode(data: SendVerifyCodeRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/verifications/email', data);
  },

  async verifyEmail(data: VerifyEmailRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/verifications/email/verify', data);
  },

  async sendPasswordResetCode(data: SendResetPasswordCodeRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/password-resets', data);
  },

  async resetPassword(data: ResetPasswordRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/password-resets/confirm', data);
  },

  async getOAuthUrl(provider: string): Promise<OAuthUrlResponse> {
    const response = await axiosInstance.get<OAuthUrlResponse>(
      `/api/v1/auth/oauth/${provider}/authorize`
    );
    return response.data;
  },

  async getOAuthConnectUrl(provider: string): Promise<OAuthUrlResponse> {
    const response = await axiosInstance.get<OAuthUrlResponse>(
      `/api/v1/auth/oauth/${provider}/authorize/connect`
    );
    return response.data;
  },
};

export const usersApi = {
  async register(data: UserCreateRequest): Promise<UserResponse> {
    const response = await axiosInstance.post<UserResponse>(
      '/api/v1/users/register',
      data
    );
    return response.data;
  },

  async getMe(): Promise<UserResponse> {
    const response = await axiosInstance.get<UserResponse>('/api/v1/users/me');
    return response.data;
  },

  async getUsers(params?: UserListParams): Promise<PageResult<UserDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<UserDTO>>(
      `/api/v1/users/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async assignRole(userId: number, data: RoleAssignRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/users/${userId}/roles`, data);
  },

  async removeRole(userId: number, roleName: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/users/${userId}/roles/${roleName}`);
  },

  async addPermissions(userId: number, data: UserPermissionRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/users/${userId}/permissions`, data);
  },

  async removePermissions(userId: number, data: UserPermissionRequest): Promise<void> {
    await axiosInstance.delete(`/api/v1/users/${userId}/permissions`, { data });
  },

  async getSessions(): Promise<SessionDTO[]> {
    const response = await axiosInstance.get<SessionDTO[]>('/api/v1/users/sessions');
    return response.data;
  },
};

export const permissionsApi = {
  async getPermissions(params?: PermissionListParams): Promise<PageResult<PermissionDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<PermissionDTO>>(
      `/api/v1/permissions/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async createPermission(data: PermissionCreateRequest): Promise<void> {
    await axiosInstance.post('/api/v1/permissions/', data);
  },

  async deletePermission(name: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/permissions/${name}`);
  },
};

export const rolesApi = {
  async getRoles(params?: RoleListParams): Promise<PageResult<RoleDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<RoleDTO>>(
      `/api/v1/roles/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async createRole(data: RoleCreateRequest): Promise<void> {
    await axiosInstance.post('/api/v1/roles/', data);
  },

  async addPermissions(roleName: string, data: RolePermissionRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/roles/${roleName}/permissions`, data);
  },

  async removePermissions(roleName: string, data: RolePermissionRequest): Promise<void> {
    await axiosInstance.delete(`/api/v1/roles/${roleName}/permissions`, { data });
  },
};

export const sessionsApi = {
  async getSessions(params?: SessionListParams): Promise<PageResult<SessionDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<SessionDTO>>(
      `/api/v1/sessions/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async deleteSession(sessionId: number): Promise<void> {
    await axiosInstance.delete(`/api/v1/sessions/${sessionId}`);
  },
};

export const profilesApi = {
  async getProfiles(params?: ProfileListParams): Promise<PageResult<ProfileDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ProfileDTO>>(
      `/api/v1/profiles/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async getProfile(profileId: number): Promise<ProfileDTO> {
    const response = await axiosInstance.get<ProfileDTO>(
      `/api/v1/profiles/${profileId}`
    );
    return response.data;
  },

  async createProfile(data: ProfileCreateRequest): Promise<void> {
    await axiosInstance.post('/api/v1/profiles/', data);
  },

  async updateProfile(profileId: number, data: ProfileUpdateRequest): Promise<void> {
    await axiosInstance.put(`/api/v1/profiles/${profileId}`, data);
  },

  async getAvatarPresignUrl(data: AvatarPreSignUrlRequest): Promise<AvatarPresignResponse> {
    const response = await axiosInstance.post<AvatarPresignResponse>(
      '/api/v1/profiles/avatar/presign',
      data
    );
    return response.data;
  },

  async uploadAvatarComplete(data: AvatarUploadCompleteRequest): Promise<void> {
    await axiosInstance.post('/api/v1/profiles/avatar/upload_complete', data);
  },

  async addContact(profileId: number, data: AddContactProfileRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/profiles/${profileId}/contacts`, data);
  },

  async removeContact(profileId: number, provideContact: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/profiles/${profileId}/${provideContact}/delete`);
  },
};

export const projectsApi = {
  async getProjects(params?: ProjectListParams): Promise<PageResult<ProjectDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ProjectDTO>>(
      `/api/v1/projects/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async getMyProjects(page?: number, pageSize?: number): Promise<PageResult<ProjectDTO>> {
    const params: any = {};
    if (page !== undefined) params.page = page;
    if (pageSize !== undefined) params.page_size = pageSize;
    const queryString = formatQueryParams(params);
    const response = await axiosInstance.get<PageResult<ProjectDTO>>(
      `/api/v1/projects/my${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async getProject(projectId: number): Promise<ProjectDTO> {
    const response = await axiosInstance.get<ProjectDTO>(
      `/api/v1/projects/${projectId}`
    );
    return response.data;
  },

  async createProject(data: ProjectCreateRequest): Promise<void> {
    await axiosInstance.post('/api/v1/projects/', data);
  },

  async updateProject(projectId: number, data: ProjectUpdateRequest): Promise<void> {
    await axiosInstance.put(`/api/v1/projects/${projectId}`, data);
  },

  async deleteProject(projectId: number): Promise<void> {
    await axiosInstance.delete(`/api/v1/projects/${projectId}`);
  },

  async getProjectPositions(projectId: number, params?: PositionListParams): Promise<PositionDTO[]> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<PositionDTO>>(
      `/api/v1/projects/${projectId}/positions${queryString ? `?${queryString}` : ''}`
    );
    return response.data.items;
  },

  async createPosition(projectId: number, data: PositionCreateRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/projects/${projectId}/positions`, data);
  },

  async inviteMember(projectId: number, data: InviteMemberRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/projects/${projectId}/invite`, data);
  },

  async acceptInvite(projectId: number): Promise<void> {
    await axiosInstance.post(`/api/v1/projects/${projectId}/members/accept`);
  },

  async updateMemberPermissions(
    projectId: number,
    userId: number,
    data: MemberUpdatePermissionsRequest
  ): Promise<void> {
    await axiosInstance.put(
      `/api/v1/projects/${projectId}/members/${userId}/permissions`,
      data
    );
  },
};

export const positionsApi = {
  async getPositions(params?: PositionListParams): Promise<PageResult<PositionDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<PositionDTO>>(
      `/api/v1/positions/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async getPosition(positionId: string): Promise<PositionDTO> {
    const response = await axiosInstance.get<PositionDTO>(
      `/api/v1/positions/${positionId}`
    );
    return response.data;
  },

  async updatePosition(positionId: string, data: PositionUpdateRequest): Promise<void> {
    await axiosInstance.put(`/api/v1/positions/${positionId}`, data);
  },

  async deletePosition(positionId: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/positions/${positionId}`);
  },

  async getApplications(
    positionId: string,
    params?: ApplicationListParams
  ): Promise<PageResult<ApplicationDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ApplicationDTO>>(
      `/api/v1/positions/${positionId}/applications${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async applyToPosition(positionId: string, data: ApplicationCreateRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/positions/${positionId}/applications`, data);
  },
};

export const applicationsApi = {
  async getApplications(params?: ApplicationListParams): Promise<PageResult<ApplicationDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ApplicationDTO>>(
      `/api/v1/applications/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async getMyApplications(params?: ApplicationListParams): Promise<PageResult<ApplicationDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ApplicationDTO>>(
      `/api/v1/applications/me${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  async approveApplication(applicationId: string): Promise<void> {
    await axiosInstance.post(`/api/v1/applications/${applicationId}/approve`);
  },

  async rejectApplication(applicationId: string): Promise<void> {
    await axiosInstance.post(`/api/v1/applications/${applicationId}/reject`);
  },

  async createApplication(positionId: string, data?: { message?: string }): Promise<void> {
    await axiosInstance.post(`/api/v1/positions/${positionId}/applications`, data || {});
  },
};

export const projectRolesApi = {
  async getProjectRoles(params?: ProjectRoleListParams): Promise<PageResult<ProjectRoleDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<ProjectRoleDTO>>(
      `/api/v1/project_roles/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },
};

export const apiClient = {
  auth: authApi,
  users: usersApi,
  permissions: permissionsApi,
  roles: rolesApi,
  sessions: sessionsApi,
  profiles: profilesApi,
  projects: projectsApi,
  positions: positionsApi,
  applications: applicationsApi,
  projectRoles: projectRolesApi,
};