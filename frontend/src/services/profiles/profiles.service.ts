import type { PageResult } from '../../types/api/common.ts';
import type {
  AvatarPresignResponse,
  ProfileDTO,
} from '../../types/api/profile.ts';
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  type QueryParamValue,
} from '../api/client.ts';

export interface CreateProfileBody {
  display_name?: string | null;
  bio?: string | null;
  skills?: string[];
  date_birthday?: string | null;
}

export async function createProfile(body: CreateProfileBody): Promise<void> {
  await apiPost<unknown>('/profiles/', { body });
}

export interface ListProfilesQuery {
  username?: string;
  display_name?: string;
  skills?: string[];
  page?: number;
  page_size?: number;
  sort?: string;
}

export async function listProfiles(
  query?: ListProfilesQuery,
): Promise<PageResult<ProfileDTO>> {
  return apiGet<PageResult<ProfileDTO>>('/profiles', {
    query: query as Record<string, QueryParamValue>,
  });
}

export async function getProfile(profileId: number): Promise<ProfileDTO> {
  return apiGet<ProfileDTO>(`/profiles/${profileId}`);
}

export interface UpdateProfileBody {
  specialization?: string;
  display_name?: string;
  bio?: string;
  skills?: string[];
  date_birthday?: string;
}

export async function updateProfile(
  profileId: number,
  body: UpdateProfileBody,
): Promise<void> {
  await apiPut<unknown>(`/profiles/${profileId}`, { body });
}

export interface AvatarPresignBody {
  filename: string;
  content_type: string;
  size: number;
}

export async function presignAvatarUpload(
  body: AvatarPresignBody,
): Promise<AvatarPresignResponse> {
  return apiPost<AvatarPresignResponse>('/profiles/avatar/presign', { body });
}

export interface AvatarUploadCompleteBody {
  key_base: string;
  size: number;
  content_type: string;
}

export async function completeAvatarUpload(
  body: AvatarUploadCompleteBody,
): Promise<string> {
  return apiPost<string>('/profiles/avatar/upload_complete', { body });
}

export async function uploadAvatar(file: File): Promise<string> {
  const presign = await presignAvatarUpload({
    filename: file.name,
    content_type: file.type || 'application/octet-stream',
    size: file.size,
  });

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
    throw new Error('Failed to upload avatar');
  }

  return completeAvatarUpload({
    key_base: presign.key_base,
    size: file.size,
    content_type: file.type || 'application/octet-stream',
  });
}

export interface AddContactBody {
  provider: string;
  contact: string;
}

export async function addProfileContact(
  profileId: number,
  body: AddContactBody,
): Promise<void> {
  await apiPost<unknown>(`/profiles/${profileId}/contacts`, { body });
}

export async function deleteProfileContact(
  profileId: number,
  provider: string,
): Promise<void> {
  await apiDelete(
    `/profiles/${profileId}/${encodeURIComponent(provider)}/delete`,
  );
}
