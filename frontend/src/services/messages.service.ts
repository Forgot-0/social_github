import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  AttachmentDownloadUrlDTO,
  ForwardMessageResult,
  MessageCursorPage,
  MessageReadDetailsPageDTO,
  SendMessageResult,
  UploadSlotDTO,
} from '../domain/types/api.types';

export interface MessagesListQuery {
  limit?: number;
  before_id?: number | null;
}

export interface MessageReadDetailsQuery {
  limit?: number;
  after_user_id?: number | null;
}

export class MessagesService {
  constructor(private readonly http: IHttpClient) {}

  requestUploadSlots(
    chatId: number,
    body: {
      uploads: {
        filename: string;
        mime_type: string;
        file_size: number;
      }[];
    },
  ): Promise<UploadSlotDTO[]> {
    return this.http.request<UploadSlotDTO[]>({
      path: `/chats/${chatId}/messages/upload`,
      method: 'POST',
      jsonBody: body,
    });
  }

  send(
    chatId: number,
    body: {
      content?: string | null;
      reply_to_id?: number | null;
      message_type?: string;
      upload_tokens?: string[];
    },
  ): Promise<SendMessageResult> {
    return this.http.request<SendMessageResult>({
      path: `/chats/${chatId}/messages/`,
      method: 'POST',
      jsonBody: body,
    });
  }

  forward(
    chatId: number,
    body: {
      source_chat_id: number;
      source_message_id: number;
      comment?: string | null;
    },
  ): Promise<ForwardMessageResult> {
    return this.http.request<ForwardMessageResult>({
      path: `/chats/${chatId}/messages/forward`,
      method: 'POST',
      jsonBody: body,
    });
  }

  list(chatId: number, q: MessagesListQuery = {}): Promise<MessageCursorPage> {
    return this.http.request<MessageCursorPage>({
      path: `/chats/${chatId}/messages/`,
      method: 'GET',
      query: {
        limit: q.limit,
        before_id: q.before_id ?? undefined,
      },
    });
  }

  attachmentDownloadUrl(
    chatId: number,
    messageId: number,
    attachmentId: string,
  ): Promise<AttachmentDownloadUrlDTO> {
    return this.http.request<AttachmentDownloadUrlDTO>({
      path: `/chats/${chatId}/messages/${messageId}/attachments/${encodeURIComponent(attachmentId)}/url`,
      method: 'GET',
    });
  }

  readDetails(
    chatId: number,
    q: MessageReadDetailsQuery = {},
  ): Promise<MessageReadDetailsPageDTO> {
    return this.http.request<MessageReadDetailsPageDTO>({
      path: `/chats/${chatId}/messages/read-details`,
      method: 'GET',
      query: {
        limit: q.limit,
        after_user_id: q.after_user_id ?? undefined,
      },
    });
  }

  edit(
    chatId: number,
    messageId: number,
    body: { content: string },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}/messages/${messageId}`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  delete(chatId: number, messageId: number): Promise<void> {
    return this.http.request<void>({
      path: `/chats/${chatId}/messages/${messageId}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }

  markRead(chatId: number, body: { message_id: number }): Promise<void> {
    return this.http.request<void>({
      path: `/chats/${chatId}/messages/read`,
      method: 'POST',
      jsonBody: body,
      parseAs: 'void',
    });
  }
}
