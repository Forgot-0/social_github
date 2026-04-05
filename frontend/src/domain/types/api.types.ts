// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AccessTokenResponse {
  access_token: string;
}

// ─── Users ───────────────────────────────────────────────────────────────────

export interface UserResponse {
  id: number;
  username: string;
  email: string;
}

export interface PermissionDTO {
  id: number;
  name: string;
}

export interface RoleDTO {
  id: number;
  name: string;
  description: string;
  security_level: number;
  permissions: PermissionDTO[];
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
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  roles: RoleDTO[];
  permissions: PermissionDTO[];
  sessions: SessionDTO[];
}

// ─── Profiles ────────────────────────────────────────────────────────────────

export interface ContactDTO {
  profile_id: number;
  provider: string;
  contact: string;
}

export interface ProfileDTO {
  id: number;
  avatars: Record<number, Record<string, string>>;
  specialization: string | null;
  display_name: string | null;
  bio: string | null;
  date_birthday: string | null;
  skills: string[];
  contacts: ContactDTO[];
}

export interface AvatarPresignResponse {
  url: string;
  fields: Record<string, string>;
  key_base: string;
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export interface ProjectRoleDTO {
  id: number;
  name: string;
  permissions: Record<string, unknown>;
}

export interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: 'public' | 'private';
  meta_data: Record<string, unknown>;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  memberships: MemberDTO[];
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
  role: ProjectRoleDTO | null;
  project: ProjectDTO | null;
}

// ─── Positions ────────────────────────────────────────────────────────────────

export interface PositionDTO {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities: string | null;
  required_skills: string[];
  is_open: boolean;
  location_type: 'remote' | 'onsite' | 'hybrid';
  expected_load: 'low' | 'medium' | 'high';
}

// ─── Applications ─────────────────────────────────────────────────────────────

export interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;
}

// ─── Chats ────────────────────────────────────────────────────────────────────

export interface MemberInfoDTO {
  user_id: number;
  role_id: number;
  is_muted: boolean;
}

export interface MemberPresenceDTO {
  user_id: number;
  is_online: boolean;
}

export interface ChatListItemDTO {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name: string | null;
  description: string | null;
  avatar_url: string | null;
  is_public: boolean;
  created_by: number;
  last_activity_at: string | null;
  unread_count: number;
  member_count: number;
}

export interface ChatDetailDTO {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name: string | null;
  description: string | null;
  avatar_url: string | null;
  is_public: boolean;
  created_by: number;
  members: MemberInfoDTO[];
  unread_count: number;
}

export interface ChatListCursorPageDTO {
  items: ChatListItemDTO[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface ChatPresenceDTO {
  chat_id: number;
  members: MemberPresenceDTO[];
  online_count: number;
}

export interface CreateChatResponse {
  chat_id: number;
}

// ─── Messages ─────────────────────────────────────────────────────────────────

export interface AttachmentDTO {
  id: string;
  message_id: number;
  chat_id: number;
  uploader_id: number;
  attachment_type: 'image' | 'video' | 'file';
  mime_type: string;
  original_filename: string;
  file_size: number;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface MessageDTO {
  id: number;
  chat_id: number;
  author_id: number | null;
  type: 'text' | 'reply' | 'system' | 'image' | 'file';
  content: string | null;
  reply_to_id: number | null;
  media_url: string | null;
  is_deleted: boolean;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
  reply_to: MessageDTO | null;
  attachments: AttachmentDTO[];
  forwarded_from_chat_id: number | null;
  forwarded_from_message_id: number | null;
}

export interface MessageCursorPage {
  items: MessageDTO[];
  next_cursor: number | null;
  has_more: boolean;
  read_cursors: Record<number, number>;
}

export interface MessageDeliveryStatusDTO {
  message_id: number;
  delivered_to: Record<number, boolean>;
}

export interface MemberReadCursorDTO {
  user_id: number;
  last_read_message_id: number;
}

export interface MessageReadDetailsPageDTO {
  items: MemberReadCursorDTO[];
  next_cursor: number | null;
  has_more: boolean;
}

export interface UploadSlotDTO {
  upload_token: string;
  upload_url: string;
  attachment_type: 'image' | 'video' | 'file';
  expires_in: number;
}

export interface AttachmentDownloadUrlDTO {
  attachment_id: string;
  url: string;
  expires_in: number;
}

export interface SendMessageResult {
  message_id: number;
  chat_id: number;
  created_at: string;
  attachment_count: number;
}

export interface ForwardMessageResult {
  message_id: number;
  chat_id: number;
  created_at: string;
  attachment_count: number;
}

// ─── LiveKit / Calls ──────────────────────────────────────────────────────────

export interface JoinTokenDTO {
  token: string;
  slug: string;
  livekit_url: string;
}

export interface LiveKitParticipantsDTO {
  identity: string;
  name: string;
  state: number;
  joined_at: number;
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
