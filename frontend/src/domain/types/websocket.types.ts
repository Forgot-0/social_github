export type WSEventType =
  | 'new_message'
  | 'message_deleted'
  | 'message_edited'
  | 'messages_read'
  | 'member_joined'
  | 'member_left'
  | 'member_kick'
  | 'typing_start'
  | 'typing_stop'
  | 'ping'
  | 'call_started'
  | 'call_joined'
  | 'call_left'
  | 'call_ended';

export interface WSEvent {
  type: WSEventType;
  chat_id: number;
  payload: Record<string, unknown>;
  ts: string;
}

export interface WSNewMessagePayload {
  id: number;
  chat_id: number;
  author_id: number | null;
  content: string | null;
  created_at: string;
  is_edited: boolean;
  reply_to_id: number | null;
  attachment_count: number;
  forwarded_from_chat_id: number | null;
  forwarded_from_message_id: number | null;
}

export interface WSModifyMessagePayload {
  id: number;
  chat_id: number;
  author_id: number;
  content: string | null;
}

export interface WSMessagesReadPayload {
  chat_id: number;
  user_id: number;
  last_read_message_id: number;
}

export interface WSTypingPayload {
  chat_id: number;
  user_id: number;
}

export interface WSMemberPayload {
  user_id: number;
  kicked_by?: number;
}

export interface WSCallStartedPayload {
  slug: string;
  started_by: string;
  username: string;
}

export interface WSCallMemberPayload {
  user_id: number | null;
  username: string;
}

export interface WSCallEndedPayload {
  duration_seconds: number;
}
