/**
 * Type-safe API Client generated from OpenAPI spec
 */

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
} from './types';

// ============================================================================
// AUTH API
// ============================================================================

export const authApi = {
  /**
   * POST /api/v1/auth/login
   * Authenticates user and returns access token
   * Server sets refresh_token in HttpOnly cookie
   */
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

  /**
   * POST /api/v1/auth/refresh
   * Refreshes access token using refresh_token cookie
   * NO BODY - server reads cookie automatically
   */
  async refresh(): Promise<AccessTokenResponse> {
    const response = await axiosInstance.post<AccessTokenResponse>(
      '/api/v1/auth/refresh'
    );
    return response.data;
  },

  /**
   * POST /api/v1/auth/logout
   * Invalidates refresh token
   * Server should clear refresh_token cookie
   */
  async logout(): Promise<void> {
    await axiosInstance.post('/api/v1/auth/logout');
  },

  /**
   * POST /api/v1/auth/verifications/email
   * Send email verification code
   */
  async sendVerificationCode(data: SendVerifyCodeRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/verifications/email', data);
  },

  /**
   * POST /api/v1/auth/verifications/email/verify
   * Verify email with token
   */
  async verifyEmail(data: VerifyEmailRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/verifications/email/verify', data);
  },

  /**
   * POST /api/v1/auth/password-resets
   * Send password reset code
   */
  async sendPasswordResetCode(data: SendResetPasswordCodeRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/password-resets', data);
  },

  /**
   * POST /api/v1/auth/password-resets/confirm
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordRequest): Promise<void> {
    await axiosInstance.post('/api/v1/auth/password-resets/confirm', data);
  },

  /**
   * GET /api/v1/auth/oauth/{provider}/authorize
   * Get OAuth authorization URL
   */
  async getOAuthUrl(provider: string): Promise<OAuthUrlResponse> {
    const response = await axiosInstance.get<OAuthUrlResponse>(
      `/api/v1/auth/oauth/${provider}/authorize`
    );
    return response.data;
  },

  /**
   * GET /api/v1/auth/oauth/{provider}/authorize/connect
   * Get OAuth connection URL for existing user
   */
  async getOAuthConnectUrl(provider: string): Promise<OAuthUrlResponse> {
    const response = await axiosInstance.get<OAuthUrlResponse>(
      `/api/v1/auth/oauth/${provider}/authorize/connect`
    );
    return response.data;
  },
};

// ============================================================================
// USERS API
// ============================================================================

export const usersApi = {
  /**
   * POST /api/v1/users/register
   * Register new user
   */
  async register(data: UserCreateRequest): Promise<UserResponse> {
    const response = await axiosInstance.post<UserResponse>(
      '/api/v1/users/register',
      data
    );
    return response.data;
  },

  /**
   * GET /api/v1/users/me
   * Get current authenticated user
   */
  async getMe(): Promise<UserResponse> {
    const response = await axiosInstance.get<UserResponse>('/api/v1/users/me');
    return response.data;
  },

  /**
   * GET /api/v1/users/
   * Get list of users with filters
   */
  async getUsers(params?: UserListParams): Promise<PageResult<UserDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<UserDTO>>(
      `/api/v1/users/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  /**
   * POST /api/v1/users/{user_id}/roles
   * Assign role to user
   */
  async assignRole(userId: number, data: RoleAssignRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/users/${userId}/roles`, data);
  },

  /**
   * DELETE /api/v1/users/{user_id}/roles/{role_name}
   * Remove role from user
   */
  async removeRole(userId: number, roleName: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/users/${userId}/roles/${roleName}`);
  },

  /**
   * POST /api/v1/users/{user_id}/permissions
   * Add permissions to user
   */
  async addPermissions(userId: number, data: UserPermissionRequest): Promise<void> {
    await axiosInstance.post(`/api/v1/users/${userId}/permissions`, data);
  },

  /**
   * DELETE /api/v1/users/{user_id}/permissions
   * Remove permissions from user
   */
  async removePermissions(
    userId: number,
    data: UserPermissionRequest
  ): Promise<void> {
    await axiosInstance.delete(`/api/v1/users/${userId}/permissions`, { data });
  },

  /**
   * GET /api/v1/users/sessions
   * Get active user sessions
   */
  async getSessions(): Promise<SessionDTO[]> {
    const response = await axiosInstance.get<SessionDTO[]>('/api/v1/users/sessions');
    return response.data;
  },
};

// ============================================================================
// PERMISSIONS API
// ============================================================================

export const permissionsApi = {
  /**
   * GET /api/v1/permissions/
   * Get list of permissions
   */
  async getPermissions(
    params?: PermissionListParams
  ): Promise<PageResult<PermissionDTO>> {
    const queryString = params ? formatQueryParams(params) : '';
    const response = await axiosInstance.get<PageResult<PermissionDTO>>(
      `/api/v1/permissions/${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  /**
   * POST /api/v1/permissions/
   * Create new permission
   */
  async createPermission(data: PermissionCreateRequest): Promise<void> {
    await axiosInstance.post('/api/v1/permissions/', data);
  },

  /**
   * DELETE /api/v1/permissions/{name}
   * Delete permission
   */
  async deletePermission(name: string): Promise<void> {
    await axiosInstance.delete(`/api/v1/permissions/${name}`);
  },
};

// ============================================================================
// Export all
// ============================================================================

export const apiClient = {
  auth: authApi,
  users: usersApi,
  permissions: permissionsApi,
};
