/**
 * Builds `WS /api/v1/chats/ws/?token=<access_token>` URL for browser WebSocket.
 * If `apiBasePath` is absolute (`https://...`), uses matching `wss://...`.
 * If it is relative (`/api/v1`), uses current host and `ws:` / `wss:` from `window.location`.
 */
export function buildChatWebSocketUrl(
  apiBasePath: string,
  accessToken: string,
): string {
  const trimmed = apiBasePath.endsWith('/')
    ? apiBasePath.slice(0, -1)
    : apiBasePath;
  const query = `token=${encodeURIComponent(accessToken)}`;

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const wsBase = trimmed.replace(/^http/, 'ws');
    return `${wsBase}/chats/ws/?${query}`;
  }

  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}${trimmed}/chats/ws/?${query}`;
  }

  return `${trimmed}/chats/ws/?${query}`;
}
