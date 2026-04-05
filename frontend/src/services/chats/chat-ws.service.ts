import { buildChatWebSocketUrl } from '../api/client.ts';

export function createChatWebSocket(accessToken: string): WebSocket {
  return new WebSocket(buildChatWebSocketUrl(accessToken));
}
