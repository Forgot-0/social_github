export interface ApiError {
  error: {
    code: string;
    message: string;
    detail?: Record<string, any> | any[];
  };
  status: number;
  request_id: string;
  timestamp: number;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AccessTokenResponse {
  access_token: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  grant_type?: string;
  scope?: string;
  client_id?: string;
  client_secret?: string;
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
  password: string;
  password_repeat: string;
  token: string;
}

export interface OAuthUrlResponse {
  url: string;
}

export interface UserCreateRequest {
  password: string;
  password_repeat: string;
  username: string;
  email: string;
}

export interface UserResponse {
  username: string;
  email: string;
  id: number;
}

export interface PermissionDTO {
  id: number;
  name: string;
}

export interface RoleDTO {
  name: string;
  description: string;
  security_level: number;
  permissions?: PermissionDTO[];
  id: number;
}

export interface SessionDTO {
  id: number;
  user_id: number;
  device_info: string;
  user_agent: string;
  last_activity: string;
  is_active: boolean;
}

export interface UserDTO {
  username: string;
  email: string;
  id: number;
  roles?: RoleDTO[];
  permissions?: PermissionDTO[];
  sessions?: SessionDTO[];
  is_active: boolean;
  is_verified: boolean;
}

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

export interface RoleAssignRequest {
  role_name: string;
}

export interface UserPermissionRequest {
  permissions?: string[];
}

export interface PermissionCreateRequest {
  name: string;
}

export interface PermissionListParams {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface RoleCreateRequest {
  name: string;
  description: string;
  security_level: number;
  permissions?: string[];
}

export interface RoleListParams {
  name?: string;
  security_level?: number;
  min_security_level?: number;
  max_security_level?: number;
  permission_names?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface RolePermissionRequest {
  permission?: string[];
}

export interface SessionListParams {
  user_id?: number;
  device_id?: string;
  last_activity_after?: string;
  last_activity_before?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface ContactDTO {
  profile_id: number;
  provider: string;
  contact: string;
}

export interface ProfileDTO {
  id: number;
  avatars: Record<string, Record<string, string>>;
  specialization: string | null;
  display_name: string | null;
  bio: string | null;
  date_birthday: string | null;
  skills: string[];
  contacts: ContactDTO[];
}

export interface ProfileCreateRequest {
  display_name?: string | null;
  bio?: string | null;
  skills?: string[] | null;
  date_birthday?: string | null;
}

export interface ProfileUpdateRequest {
  specialization?: string | null;
  display_name?: string | null;
  bio?: string | null;
  skills?: string[] | null;
  date_birthday?: string | null;
}

export interface ProfileListParams {
  display_name?: string;
  skills?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface AddContactProfileRequest {
  provider: string;
  contact: string;
}

export interface AvatarPreSignUrlRequest {
  filename: string;
  size: number;
  content_type: string;
}

export interface AvatarPresignResponse {
  url: string;
  fields: Record<string, string>;
  key_base: string;
}

export interface AvatarUploadCompleteRequest {
  key_base: string;
  size: number;
  content_type: string;
}

export interface MemberDTO {
  id: number;
  project_id: number;
  user_id: number;
  role_id: number | null;
  status: string;
  invited_by: number | null;
  joined_at: string | null;
  permissions_overrides: Record<string, any>;
}

export interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: string;
  meta_data: Record<string, any>;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  memberships?: MemberDTO[];
}

export interface ProjectCreateRequest {
  name: string;
  slug: string;
  small_description?: string | null;
  description?: string | null;
  visibility?: string | null;
  meta_data?: Record<string, any> | null;
  tags?: string[] | null;
}

export interface ProjectUpdateRequest {
  name?: string | null;
  description?: string | null;
  visibility?: string | null;
  meta_data?: Record<string, any> | null;
  tags?: string[] | null;
}

export interface ProjectListParams {
  name?: string;
  slug?: string;
  tags?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface InviteMemberRequest {
  user_id: number;
  role_id: number;
  permissions_overrides?: Record<string, any> | null;
}

export interface MemberUpdatePermissionsRequest {
  permissions_overrides: Record<string, any>;
}

export type PositionLocationType = 'remote' | 'onsite' | 'hybrid';
export type PositionLoad = 'low' | 'medium' | 'high';

export interface PositionDTO {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities: string | null;
  required_skills: string[];
  is_open: boolean;
  location_type: string;
  expected_load: string;
}

export interface PositionCreateRequest {
  title: string;
  description: string;
  responsibilities?: string | null;
  required_skills?: string[] | null;
  location_type?: string | null;
  expected_load?: string | null;
}

export interface PositionUpdateRequest {
  title?: string | null;
  description?: string | null;
  responsibilities?: string | null;
  required_skills?: string[] | null;
  location_type?: string | null;
  expected_load?: string | null;
}

export interface PositionListParams {
  project_id?: number;
  title?: string;
  required_skills?: string[];
  is_open?: boolean;
  location_type?: PositionLocationType;
  expected_load?: PositionLoad;
  page?: number;
  page_size?: number;
  sort?: string;
}

export type ApplicationStatus = 'pending' | 'accepted' | 'rejected';

export interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: string;
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;
}

export interface ApplicationCreateRequest {
  message?: string | null;
}

export interface ApplicationListParams {
  project_id?: number;
  position_id?: string;
  candidate_id?: number;
  status?: ApplicationStatus;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface ProjectRoleDTO {
  id: number;
  name: string;
  permissions: Record<string, any>;
}

export interface ProjectRoleListParams {
  name?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}

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
  DUPLICATE_ROLE = 'DUPLICATE_ROLE',
  INVALID_ROLE_NAME = 'INVALID_ROLE_NAME',
  NOT_EXIST_PROVIDER_OAUTH = 'NOT_EXIST_PROVIDER_OAUTH',
  OAUTH_STATE_NOT_FOUND = 'OAUTH_STATE_NOT_FOUND',
  LINKED_ANOTHER_USER_OAUTH = 'LINKED_ANOTHER_USER_OAUTH',
  NOT_FOUND_PROFILE = 'NOT_FOUND_PROFILE',
  NOT_FOUND_PROJECT = 'NOT_FOUND_PROJECT',
}
