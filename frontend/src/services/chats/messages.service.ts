import type {
  AttachmentDownloadUrlDTO,
  ForwardMessageResult,
  MessageCursorPage,
  MessageReadDetailsPageDTO,
  SendMessageResult,
  UploadSlotDTO,
} from '../../types/api/message.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  type QueryParamValue,
} from '../api/client.ts';

function messagesPath(chatId: number, suffix = ''): string {
  return `/chats/${chatId}/messages${suffix}`;
}

export interface MessageUploadDescriptor {
  filename: string;
  mime_type: string;
  file_size: number;
}

export async function createMessageUploadSlots(
  chatId: number,
  uploads: MessageUploadDescriptor[],
): Promise<UploadSlotDTO[]> {
  return apiPost<UploadSlotDTO[]>(messagesPath(chatId, '/upload'), {
    body: { uploads },
  });
}

export interface SendMessageBody {
  content?: string | null;
  reply_to_id?: number | null;
  message_type?: string;
  upload_tokens?: string[];
}

export async function sendMessage(
  chatId: number,
  body: SendMessageBody,
): Promise<SendMessageResult> {
  return apiPost<SendMessageResult>(messagesPath(chatId, '/'), { body });
}

export interface ForwardMessageBody {
  source_chat_id: number;
  source_message_id: number;
  comment?: string | null;
}

export async function forwardMessage(
  chatId: number,
  body: ForwardMessageBody,
): Promise<ForwardMessageResult> {
  return apiPost<ForwardMessageResult>(messagesPath(chatId, '/forward'), {
    body,
  });
}

export interface ListMessagesQuery {
  limit?: number;
  before_id?: number | null;
}

export async function listMessages(
  chatId: number,
  query?: ListMessagesQuery,
): Promise<MessageCursorPage> {
  return apiGet<MessageCursorPage>(messagesPath(chatId, '/'), {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function getAttachmentDownloadUrl(
  chatId: number,
  messageId: number,
  attachmentId: string,
): Promise<AttachmentDownloadUrlDTO> {
  return apiGet<AttachmentDownloadUrlDTO>(
    messagesPath(
      chatId,
      `/${messageId}/attachments/${encodeURIComponent(attachmentId)}/url`,
    ),
  );
}

export interface ListMessageReadDetailsQuery {
  limit?: number;
  after_user_id?: number | null;
}

export async function listMessageReadDetails(
  chatId: number,
  query?: ListMessageReadDetailsQuery,
): Promise<MessageReadDetailsPageDTO> {
  return apiGet<MessageReadDetailsPageDTO>(
    messagesPath(chatId, '/read-details'),
    {
      query: query as Record<string, QueryParamValue>,
    },
  );
}

export async function editMessage(
  chatId: number,
  messageId: number,
  content: string,
): Promise<void> {
  await apiPut<unknown>(messagesPath(chatId, `/${messageId}`), {
    body: { content },
  });
}

export async function deleteMessage(
  chatId: number,
  messageId: number,
): Promise<void> {
  await apiDelete(messagesPath(chatId, `/${messageId}`));
}

export async function markMessagesRead(
  chatId: number,
  messageId: number,
): Promise<void> {
  await apiPost<unknown>(messagesPath(chatId, '/read'), {
    body: { message_id: messageId },
  });
}
