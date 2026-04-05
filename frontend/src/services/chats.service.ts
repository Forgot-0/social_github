import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  ChatDetailDTO,
  ChatListCursorPageDTO,
  ChatPresenceDTO,
  CreateChatResponse,
  JoinTokenDTO,
  LiveKitParticipantsDTO,
  MessageDeliveryStatusDTO,
} from '../domain/types/api.types';

export interface ChatsMyQuery {
  limit?: number;
  cursor?: string | null;
}

export class ChatsService {
  constructor(private readonly http: IHttpClient) {}

  create(body: {
    chat_type: 'direct' | 'group' | 'channel';
    member_ids?: number[];
    name?: string | null;
    description?: string | null;
    is_public?: boolean;
  }): Promise<CreateChatResponse> {
    return this.http.request<CreateChatResponse>({
      path: '/chats/',
      method: 'POST',
      jsonBody: body,
    });
  }

  my(q: ChatsMyQuery = {}): Promise<ChatListCursorPageDTO> {
    return this.http.request<ChatListCursorPageDTO>({
      path: '/chats/my',
      method: 'GET',
      query: {
        limit: q.limit,
        cursor: q.cursor ?? undefined,
      },
    });
  }

  get(chatId: number): Promise<ChatDetailDTO> {
    return this.http.request<ChatDetailDTO>({
      path: `/chats/${chatId}`,
      method: 'GET',
    });
  }

  update(
    chatId: number,
    body: {
      name?: string | null;
      description?: string | null;
      avatar_url?: string | null;
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  addMember(
    chatId: number,
    body: { user_id: number; role_id: number },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}/members`,
      method: 'POST',
      jsonBody: body,
    });
  }

  removeMember(chatId: number, userId: number): Promise<void> {
    return this.http.request<void>({
      path: `/chats/${chatId}/members/${userId}`,
      method: 'DELETE',
      parseAs: 'void',
    });
  }

  updateMemberRole(
    chatId: number,
    userId: number,
    body: { role_id: number },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}/members/${userId}/role`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  banMember(
    chatId: number,
    userId: number,
    body: { ban?: boolean } = {},
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}/members/${userId}/ban`,
      method: 'POST',
      jsonBody: body,
    });
  }

  leave(chatId: number): Promise<void> {
    return this.http.request<void>({
      path: `/chats/${chatId}/leave`,
      method: 'POST',
      parseAs: 'void',
    });
  }

  presence(chatId: number): Promise<ChatPresenceDTO> {
    return this.http.request<ChatPresenceDTO>({
      path: `/chats/${chatId}/presence`,
      method: 'GET',
    });
  }

  messageDelivery(
    chatId: number,
    messageId: number,
  ): Promise<MessageDeliveryStatusDTO> {
    return this.http.request<MessageDeliveryStatusDTO>({
      path: `/chats/${chatId}/messages/${messageId}/delivery`,
      method: 'GET',
    });
  }

  joinCall(chatId: number): Promise<JoinTokenDTO> {
    return this.http.request<JoinTokenDTO>({
      path: `/chats/${chatId}/calls/join`,
      method: 'POST',
    });
  }

  callParticipants(chatId: number): Promise<LiveKitParticipantsDTO[]> {
    return this.http.request<LiveKitParticipantsDTO[]>({
      path: `/chats/${chatId}/calls/participants`,
      method: 'GET',
    });
  }

  muteCallParticipant(
    chatId: number,
    userId: number,
    body: { muted?: boolean } = {},
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/chats/${chatId}/calls/participants/${userId}/mute`,
      method: 'PUT',
      jsonBody: body,
    });
  }
}
