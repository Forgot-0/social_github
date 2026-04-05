import type { IHttpClient } from '../application/ports/http-client.port';
import type {
  AvatarPresignResponse,
  PageResult,
  ProfileDTO,
} from '../domain/types/api.types';

export interface ProfilesListQuery {
  username?: string;
  display_name?: string;
  skills?: readonly string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export class ProfilesService {
  constructor(private readonly http: IHttpClient) {}

  create(body: {
    display_name?: string | null;
    bio?: string | null;
    skills?: string[];
    date_birthday?: string | null;
  }): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: '/profiles/',
      method: 'POST',
      jsonBody: body,
    });
  }

  list(q: ProfilesListQuery = {}): Promise<PageResult<ProfileDTO>> {
    const { skills, page, page_size, sort, ...rest } = q;
    return this.http.request<PageResult<ProfileDTO>>({
      path: '/profiles/',
      method: 'GET',
      query: { ...rest, page, page_size, sort },
      queryMulti: { skills },
    });
  }

  get(profileId: number): Promise<ProfileDTO> {
    return this.http.request<ProfileDTO>({
      path: `/profiles/${profileId}`,
      method: 'GET',
    });
  }

  update(
    profileId: number,
    body: {
      specialization?: string | null;
      display_name?: string | null;
      bio?: string | null;
      skills?: string[];
      date_birthday?: string | null;
    },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/profiles/${profileId}`,
      method: 'PUT',
      jsonBody: body,
    });
  }

  avatarPresign(body: {
    filename: string;
    content_type: string;
    size: number;
  }): Promise<AvatarPresignResponse> {
    return this.http.request<AvatarPresignResponse>({
      path: '/profiles/avatar/presign',
      method: 'POST',
      jsonBody: body,
    });
  }

  avatarUploadComplete(body: {
    key_base: string;
    size: number;
    content_type: string;
  }): Promise<string> {
    return this.http.request<string>({
      path: '/profiles/avatar/upload_complete',
      method: 'POST',
      jsonBody: body,
      parseAs: 'text',
    });
  }

  addContact(
    profileId: number,
    body: { provider: string; contact: string },
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/profiles/${profileId}/contacts`,
      method: 'POST',
      jsonBody: body,
    });
  }

  deleteContact(
    profileId: number,
    providerContact: string,
  ): Promise<Record<string, never>> {
    return this.http.request<Record<string, never>>({
      path: `/profiles/${profileId}/${encodeURIComponent(providerContact)}/delete`,
      method: 'DELETE',
    });
  }
}
