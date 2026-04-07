const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ApiError {
  error: {
    code: string;
    message: string;
    detail?: unknown;
  };
  status: number;
  request_id?: string;
  timestamp?: string | number;
}

type Primitive = string | number | boolean;
type QueryValue = Primitive | Primitive[] | null | undefined;
type QueryParams = Record<string, QueryValue>;

function isFormData(value: unknown): value is FormData {
  return typeof FormData !== 'undefined' && value instanceof FormData;
}

function buildQuery(params?: QueryParams): string {
  if (!params) return '';

  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;

    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== '') {
          searchParams.append(key, String(item));
        }
      });
      return;
    }

    searchParams.append(key, String(value));
  });

  const query = searchParams.toString();
  return query ? `?${query}` : '';
}

async function parseResponseBody(response: Response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get('content-type') || '';
  const text = await response.text();

  if (!text) return null;

  if (contentType.includes('application/json')) {
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  return text;
}

function normalizeApiError(payload: unknown, status: number): ApiError {
  if (
    payload &&
    typeof payload === 'object' &&
    'error' in payload &&
    (payload as any).error &&
    typeof (payload as any).error === 'object'
  ) {
    return payload as ApiError;
  }

  if (typeof payload === 'string' && payload.trim()) {
    return {
      error: {
        code: 'HTTP_ERROR',
        message: payload,
      },
      status,
    };
  }

  return {
    error: {
      code: 'HTTP_ERROR',
      message: `HTTP ${status}`,
    },
    status,
  };
}

class ApiClient {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.loadToken();
  }

  private loadToken() {
    this.accessToken = localStorage.getItem('access_token');
  }

  private saveToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('access_token', token);
  }

  resetAuth() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
  }

  async restoreSession() {
    if (this.accessToken) {
      return { access_token: this.accessToken };
    }

    try {
      return await this.refreshToken();
    } catch {
      this.resetAuth();
      return null;
    }
  }

  private async request<T = any>(endpoint: string, options: RequestInit = {}, retry = true): Promise<T> {
    const headers = new Headers(options.headers || undefined);
    const hasBody = options.body !== undefined && options.body !== null;

    if (hasBody && !isFormData(options.body) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    if (this.accessToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    const payload = await parseResponseBody(response);

    if (!response.ok) {
      const error = normalizeApiError(payload, response.status);

      if (
        retry &&
        endpoint !== '/auth/refresh' &&
        ['EXPIRED_TOKEN', 'INVALID_TOKEN'].includes(error.error.code)
      ) {
        try {
          await this.refreshToken();
          return this.request<T>(endpoint, options, false);
        } catch {
          this.resetAuth();
          throw error;
        }
      }

      throw error;
    }

    return payload as T;
  }

  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: formData,
    });

    this.saveToken(response.access_token);
    return response;
  }

  async register(data: {
    username: string;
    email: string;
    password: string;
    repeat_password: string;
  }) {
    return this.request('/users/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async refreshToken() {
    const response = await this.request<{ access_token: string }>('/auth/refresh', {
      method: 'POST',
    });
    this.saveToken(response.access_token);
    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.resetAuth();
    }
  }

  async getCurrentUser() {
    return this.request('/users/me');
  }

  async getUsers(params?: QueryParams) {
    return this.request(`/users/${buildQuery(params)}`);
  }

  async getProfile(id: number) {
    return this.request(`/profiles/${id}`);
  }

  async getProfiles(params?: QueryParams) {
    return this.request(`/profiles${buildQuery(params)}`);
  }

  async createProfile(data: {
    display_name?: string;
    bio?: string;
    skills?: string[];
    date_birthday?: string;
  }) {
    return this.request('/profiles/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProfile(id: number, data: {
    display_name?: string;
    bio?: string;
    specialization?: string;
    skills?: string[];
    date_birthday?: string;
  }) {
    return this.request(`/profiles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getAvatarPresign(file: File) {
    return this.request<{
      url: string;
      fields: Record<string, string>;
      key_base: string;
    }>('/profiles/avatar/presign', {
      method: 'POST',
      body: JSON.stringify({
        filename: file.name,
        content_type: file.type || 'image/jpeg',
        size: file.size,
      }),
    });
  }

  async completeAvatarUpload(payload: { key_base: string; size: number; content_type: string }) {
    return this.request('/profiles/avatar/upload_complete', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async uploadAvatar(file: File) {
    const presign = await this.getAvatarPresign(file);

    if (!presign?.url || !presign?.fields || !presign?.key_base) {
      throw {
        error: {
          code: 'INVALID_PRESIGN_RESPONSE',
          message: 'Backend вернул некорректный ответ для загрузки аватара',
        },
        status: 500,
      } satisfies ApiError;
    }

    const formData = new FormData();
    Object.entries(presign.fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    formData.append('file', file);

    const uploadResponse = await fetch(presign.url, {
      method: 'POST',
      body: formData,
    });

    if (!uploadResponse.ok) {
      throw {
        error: {
          code: 'AVATAR_UPLOAD_FAILED',
          message: 'Не удалось загрузить файл аватара в хранилище',
        },
        status: uploadResponse.status,
      } satisfies ApiError;
    }

    return this.completeAvatarUpload({
      key_base: presign.key_base,
      size: file.size,
      content_type: file.type || 'image/jpeg',
    });
  }

  async getProjects(params?: QueryParams) {
    return this.request(`/projects${buildQuery(params)}`);
  }

  async getMyProjects(params?: QueryParams) {
    return this.request(`/projects/my${buildQuery(params)}`);
  }

  async getProject(id: number) {
    return this.request(`/projects/${id}`);
  }

  async createProject(data: {
    name: string;
    slug: string;
    small_description?: string;
    description?: string;
    visibility?: 'public' | 'private';
    tags?: string[];
    meta_data?: Record<string, unknown>;
  }) {
    return this.request('/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProject(id: number, data: Record<string, unknown>) {
    return this.request(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: number) {
    return this.request<void>(`/projects/${id}`, { method: 'DELETE' });
  }

  async getProjectPositions(projectId: number, params?: QueryParams) {
    return this.request(`/projects/${projectId}/positions${buildQuery(params)}`);
  }

  async createPosition(projectId: number, data: Record<string, unknown>) {
    return this.request(`/projects/${projectId}/positions`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async inviteToProject(
    projectId: number,
    data: { user_id: number; role_id?: number; permissions_overrides?: Record<string, boolean> }
  ) {
    return this.request(`/projects/${projectId}/invite`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async acceptProjectInvite(projectId: number) {
    return this.request(`/projects/${projectId}/members/accept`, { method: 'POST' });
  }

  async updateMemberPermissions(projectId: number, userId: number, permissions_overrides: Record<string, boolean>) {
    return this.request(`/projects/${projectId}/members/${userId}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ permissions_overrides }),
    });
  }

  // Эти ручки не описаны явно в текущей доке, но используются для управления составом проекта.
  async updateProjectMemberRole(projectId: number, userId: number, role_id: number) {
    return this.request(`/projects/${projectId}/members/${userId}/role/`, {
      method: 'PUT',
      body: JSON.stringify({ role_id }),
    });
  }

  async removeProjectMember(projectId: number, userId: number) {
    return this.request<void>(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  }

  async getProjectRoles(params?: QueryParams) {
    return this.request(`/project_roles/${buildQuery(params)}`);
  }

  async getPositions(params?: QueryParams) {
    return this.request(`/positions${buildQuery(params)}`);
  }

  async getPosition(id: string) {
    return this.request(`/positions/${id}`);
  }

  async updatePosition(id: string, data: Record<string, unknown>) {
    return this.request(`/positions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePosition(id: string) {
    return this.request<void>(`/positions/${id}`, { method: 'DELETE' });
  }

  async applyToPosition(positionId: string, message?: string) {
    return this.request(`/positions/${positionId}/applications`, {
      method: 'POST',
      body: JSON.stringify({ message: message || null }),
    });
  }

  async getApplications(params?: QueryParams) {
    return this.request(`/applications/${buildQuery(params)}`);
  }

  async getMyApplications(params?: QueryParams) {
    return this.request(`/applications/me${buildQuery(params)}`);
  }

  async approveApplication(id: string) {
    return this.request(`/applications/${id}/approve`, { method: 'POST' });
  }

  async rejectApplication(id: string) {
    return this.request(`/applications/${id}/reject`, { method: 'POST' });
  }

  async getChats(params?: { limit?: number; cursor?: string | null }) {
    return this.request(`/chats/my${buildQuery(params as QueryParams)}`);
  }

  async createChat(data: {
    chat_type: 'direct' | 'group' | 'channel';
    member_ids?: number[];
    name?: string | null;
    description?: string | null;
    is_public?: boolean;
  }) {
    return this.request<{ chat_id: number }>(`/chats/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getChat(chatId: number) {
    return this.request(`/chats/${chatId}`);
  }

  async getChatMessages(chatId: number, params?: { limit?: number; before_id?: number | null }) {
    return this.request(`/chats/${chatId}/messages${buildQuery(params as QueryParams)}`);
  }

  async sendMessage(chatId: number, data: {
    content?: string | null;
    reply_to_id?: number | null;
    message_type?: string;
    upload_tokens?: string[];
  }) {
    return this.request(`/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content: data.content ?? null,
        reply_to_id: data.reply_to_id ?? null,
        message_type: data.message_type || 'text',
        upload_tokens: data.upload_tokens ?? [],
      }),
    });
  }

  async markMessagesRead(chatId: number, messageId: number) {
    return this.request(`/chats/${chatId}/messages/read`, {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId }),
    });
  }

  getWebSocketUrl(): string {
    const token = this.accessToken || '';
    const wsProtocol = this.baseURL.startsWith('https') ? 'wss' : 'ws';
    const baseUrl = this.baseURL.replace(/^https?:\/\//, '').replace('/api/v1', '');
    return `${wsProtocol}://${baseUrl}/api/v1/chats/ws/?token=${encodeURIComponent(token)}`;
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }
}

export const api = new ApiClient(API_BASE_URL);
export type { ApiError, QueryParams };
