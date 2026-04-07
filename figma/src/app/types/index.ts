export interface User {
  id: number;
  username: string;
  email: string;
  is_active?: boolean;
  is_verified?: boolean;
}

export interface ProfileAvatarVariants {
  [size: string]: { url: string } | string;
}

export interface Profile {
  id: number;
  display_name?: string;
  bio?: string;
  specialization?: string;
  date_birthday?: string;
  skills: string[];
  contacts: Contact[];
  avatars?: ProfileAvatarVariants;
}

export interface Contact {
  provider: string;
  contact: string;
}

export interface ProjectMembership {
  id?: number;
  project_id?: number;
  user_id: number;
  role_id?: number;
  role?: {
    id?: number;
    name?: string;
    permissions?: Record<string, boolean>;
  } | string;
  status?: string;
  invited_by?: number;
  joined_at?: string | null;
  permissions_overrides?: Record<string, boolean>;
  username?: string;
}

export interface Project {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description?: string;
  full_description?: string;
  description?: string;
  visibility: 'public' | 'private';
  tags: string[];
  meta_data?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
  memberships: ProjectMembership[];
}

export interface Position {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities?: string;
  required_skills: string[];
  is_open: boolean;
  location_type: 'remote' | 'onsite' | 'hybrid';
  expected_load: 'low' | 'medium' | 'high';
}

export interface Application {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message?: string | null;
  decided_by?: number | null;
  decided_at?: string | null;
}

export interface ChatListItem {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name?: string | null;
  description?: string | null;
  avatar_url?: string | null;
  is_public?: boolean;
  created_by?: number;
  last_activity_at?: string;
  unread_count?: number;
  member_count?: number;
}

export interface ChatDetailMember {
  user_id: number;
  role_id?: number;
  is_muted?: boolean;
}

export interface ChatDetail {
  id: number;
  type: 'direct' | 'group' | 'channel';
  name?: string | null;
  description?: string | null;
  avatar_url?: string | null;
  members: ChatDetailMember[];
  unread_count?: number;
}

export interface MessageAttachment {
  id?: string;
  attachment_id?: string;
  file_name?: string;
  mime_type?: string;
}

export interface Message {
  id: number;
  chat_id: number;
  author_id: number | null;
  type: string;
  content: string | null;
  reply_to_id?: number | null;
  media_url?: string | null;
  is_deleted?: boolean;
  is_edited?: boolean;
  created_at: string;
  updated_at?: string;
  attachments?: MessageAttachment[];
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface CursorPage<T, C = string | number | null> {
  items: T[];
  next_cursor?: C | null;
  has_more?: boolean;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    detail?: unknown;
  };
  status: number;
  request_id?: string;
  timestamp?: string | number;
}
