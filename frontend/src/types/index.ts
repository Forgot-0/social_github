// ─── Auth ────────────────────────────────────────────────────────────────────

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
  code: string;
  email: string;
}

export interface SendResetPasswordCodeRequest {
  email: string;
}

export interface ResetPasswordRequest {
  code: string;
  email: string;
  new_password: string;
}

// ─── OAuth ───────────────────────────────────────────────────────────────────

export interface OAuthUrlResponse {
  authorization_url: string;
}

// ─── Users ───────────────────────────────────────────────────────────────────

export interface UserCreateRequest {
  password: string;
  password_repeat: string;
  username: string;
  email: string;
}

export interface UserDTO {
  id: number;
  username: string;
  email: string;
  roles?: RoleDTO[];
  permissions?: PermissionDTO[];
  sessions?: SessionDTO[];
  is_active: boolean;
  is_verified: boolean;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
}

export interface UserPermissionRequest {
  permissions: string[];
}

// ─── Roles & Permissions ─────────────────────────────────────────────────────

export interface RoleDTO {
  id: number;
  name: string;
  description: string;
  security_level: number;
  permissions?: PermissionDTO[];
}

export interface RoleCreateRequest {
  name: string;
  description: string;
  security_level: number;
  permissions?: string[];
}

export interface RoleAssignRequest {
  role_name: string;
}

export interface RolePermissionRequest {
  permission: string[];
}

export interface PermissionDTO {
  id: number;
  name: string;
}

export interface PermissionCreateRequest {
  name: string;
}

// ─── Sessions ────────────────────────────────────────────────────────────────

export interface SessionDTO {
  id: number;
  user_id: number;
  device_info: string;
  user_agent: string;
  last_activity: string;
  is_active: boolean;
}

// ─── Profiles ────────────────────────────────────────────────────────────────

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

export interface ContactDTO {
  profile_id: number;
  provider: string;
  contact: string;
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
  upload_url: string;
  key_base: string;
}

export interface AvatarUploadCompleteRequest {
  key_base: string;
  size: number;
  content_type: string;
}

// ─── Projects ────────────────────────────────────────────────────────────────

export interface ProjectRoleDTO {
  id: number;
  name: string;
  permissions: Record<string, boolean>;
}

export interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: string;
  meta_data: Record<string, unknown>;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  memberships: MemberDTO[];
}

export interface ProjectCreateRequest {
  name: string;
  slug: string;
  description?: string | null;
  visibility?: string | null;
  meta_data?: Record<string, unknown> | null;
  tags?: string[] | null;
}

export interface ProjectUpdateRequest {
  name?: string | null;
  description?: string | null;
  visibility?: string | null;
  meta_data?: Record<string, unknown> | null;
  tags?: string[] | null;
}

export interface MemberDTO {
  id: number;
  project_id: number;
  user_id: number;
  role_id: number | null;
  status: string;
  invited_by: number | null;
  joined_at: string | null;
  permissions_overrides: Record<string, unknown>;
}

export interface InviteMemberRequest {
  user_id: number;
  role_id: number;
  permissions_overrides?: Record<string, unknown> | null;
}

export interface MemberUpdatePermissionsRequest {
  permissions_overrides: Record<string, unknown>;
}

// ─── Positions ───────────────────────────────────────────────────────────────

export type PositionLoad = "low" | "medium" | "high";
export type PositionLocationType = "remote" | "onsite" | "hybrid";

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

// ─── Applications ────────────────────────────────────────────────────────────

export type ApplicationStatus = "pending" | "accepted" | "rejected";

export interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: ApplicationStatus | string;
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;
}

export interface ApplicationCreateRequest {
  message?: string | null;
}

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Error ───────────────────────────────────────────────────────────────────

export interface ErrorResponse {
  detail: string;
}

// ─── Pagination Params ───────────────────────────────────────────────────────

export interface PaginationParams {
  page?: number;
  page_size?: number;
}
