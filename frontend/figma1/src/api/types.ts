/**
 * AUTO-GENERATED TypeScript types from OpenAPI spec
 * DO NOT EDIT MANUALLY
 */

// ============================================================================
// Common Types
// ============================================================================

export interface ApiError {
  error: {
    code: string;
    message: string;
    detail: Record<string, any>;
  };
  status: number;
  request_id: string;
  timestamp: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Auth Types
// ============================================================================

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SendVerifyCodeRequest {
  email: string;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface SendResetPasswordCodeRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  repeat_password: string;
}

export interface OAuthUrlResponse {
  url: string;
}

// ============================================================================
// User Types
// ============================================================================

export interface UserResponse {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserDTO {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  email: string;
  username: string;
  password: string;
  repeat_password: string;
}

export interface UserPermissionRequest {
  permissions: string[];
}

// ============================================================================
// Role Types
// ============================================================================

export interface RoleAssignRequest {
  role_name: string;
}

// ============================================================================
// Permission Types
// ============================================================================

export interface PermissionDTO {
  name: string;
  description?: string;
  created_at: string;
}

export interface PermissionCreateRequest {
  name: string;
  description?: string;
}

// ============================================================================
// Session Types
// ============================================================================

export interface SessionDTO {
  id: number;
  user_id: number;
  device: string;
  ip_address: string;
  user_agent: string;
  created_at: string;
  last_activity: string;
  is_active: boolean;
}

// ============================================================================
// Query Parameter Types
// ============================================================================

export interface UserListParams {
  email?: string;
  username?: string;
  is_active?: boolean;
  is_verified?: boolean;
  is_deleted?: boolean;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
  has_oauth_accounts?: boolean;
  has_sessions?: boolean;
  role_names?: string[];
  permission_names?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface PermissionListParams {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

// ============================================================================
// Error Code Types (для type-safe обработки ошибок)
// ============================================================================

export enum ErrorCode {
  WRONG_LOGIN_DATA = 'WRONG_LOGIN_DATA',
  INVALID_TOKEN = 'INVALID_TOKEN',
  EXPIRED_TOKEN = 'EXPIRED_TOKEN',
  NOT_FOUND_OR_INACTIVE_SESSION = 'NOT_FOUND_OR_INACTIVE_SESSION',
  NOT_FOUND_USER = 'NOT_FOUND_USER',
  PASSWORD_MISMATCH = 'PASSWORD_MISMATCH',
  DUPLICATE_USER = 'DUPLICATE_USER',
  ACCESS_DENIED = 'ACCESS_DENIED',
  NOT_FOUND_PERMISSIONS = 'NOT_FOUND_PERMISSIONS',
  PROTECTED_PERMISSION = 'PROTECTED_PERMISSION',
  NOT_FOUND_ROLE = 'NOT_FOUND_ROLE',
  NOT_EXIST_PROVIDER_OAUTH = 'NOT_EXIST_PROVIDER_OAUTH',
  OAUTH_STATE_NOT_FOUND = 'OAUTH_STATE_NOT_FOUND',
  LINKED_ANOTHER_USER_OAUTH = 'LINKED_ANOTHER_USER_OAUTH',
}
