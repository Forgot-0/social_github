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
