import type {
  ChatDetailDTO,
  ChatListCursorPageDTO,
  ChatPresenceDTO,
  CreateChatResponse,
} from '../../types/api/chat.ts';
import type {
  JoinTokenDTO,
  LiveKitParticipantsDTO,
} from '../../types/api/livekit.ts';
import type { MessageDeliveryStatusDTO } from '../../types/api/message.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  type QueryParamValue,
} from '../api/client.ts';

export interface CreateChatBody {
  chat_type: 'direct' | 'group' | 'channel';
  member_ids?: number[];
  name?: string | null;
  description?: string | null;
  is_public?: boolean;
}

export async function createChat(
  body: CreateChatBody,
): Promise<CreateChatResponse> {
  return apiPost<CreateChatResponse>('/chats/', { body });
}

export interface ListMyChatsQuery {
  limit?: number;
  cursor?: string | null;
}

export async function listMyChats(
  query?: ListMyChatsQuery,
): Promise<ChatListCursorPageDTO> {
  return apiGet<ChatListCursorPageDTO>('/chats/my', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function getChat(chatId: number): Promise<ChatDetailDTO> {
  return apiGet<ChatDetailDTO>(`/chats/${chatId}`);
}

export interface UpdateChatBody {
  name?: string;
  description?: string;
  avatar_url?: string;
}

export async function updateChat(
  chatId: number,
  body: UpdateChatBody,
): Promise<void> {
  await apiPut<unknown>(`/chats/${chatId}`, { body });
}

export interface InviteChatMemberBody {
  user_id: number;
  role_id: number;
}

export async function inviteChatMember(
  chatId: number,
  body: InviteChatMemberBody,
): Promise<void> {
  await apiPost<unknown>(`/chats/${chatId}/members`, { body });
}

export async function removeChatMember(
  chatId: number,
  userId: number,
): Promise<void> {
  await apiDelete(`/chats/${chatId}/members/${userId}`);
}

export async function setChatMemberRole(
  chatId: number,
  userId: number,
  roleId: number,
): Promise<void> {
  await apiPut<unknown>(`/chats/${chatId}/members/${userId}/role`, {
    body: { role_id: roleId },
  });
}

export interface BanChatMemberBody {
  ban?: boolean;
}

export async function setChatMemberBan(
  chatId: number,
  userId: number,
  body: BanChatMemberBody = {},
): Promise<void> {
  await apiPost<unknown>(`/chats/${chatId}/members/${userId}/ban`, { body });
}

export async function leaveChat(chatId: number): Promise<void> {
  await apiPost<unknown>(`/chats/${chatId}/leave`, { body: {} });
}

export async function getChatPresence(
  chatId: number,
): Promise<ChatPresenceDTO> {
  return apiGet<ChatPresenceDTO>(`/chats/${chatId}/presence`);
}

export async function getMessageDeliveryStatus(
  chatId: number,
  messageId: number,
): Promise<MessageDeliveryStatusDTO> {
  return apiGet<MessageDeliveryStatusDTO>(
    `/chats/${chatId}/messages/${messageId}/delivery`,
  );
}

export async function joinChatCall(chatId: number): Promise<JoinTokenDTO> {
  return apiPost<JoinTokenDTO>(`/chats/${chatId}/calls/join`, { body: {} });
}

export async function listChatCallParticipants(
  chatId: number,
): Promise<LiveKitParticipantsDTO[]> {
  return apiGet<LiveKitParticipantsDTO[]>(
    `/chats/${chatId}/calls/participants`,
  );
}

export interface MuteCallParticipantBody {
  muted?: boolean;
}

export async function setCallParticipantMute(
  chatId: number,
  userId: number,
  body: MuteCallParticipantBody = {},
): Promise<void> {
  await apiPut<unknown>(`/chats/${chatId}/calls/participants/${userId}/mute`, {
    body,
  });
}
