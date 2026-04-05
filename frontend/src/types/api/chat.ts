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
