import type { AccessTokenResponse } from '../../types/api/auth.ts';
import {
  apiGet,
  apiPost,
  apiPostForm,
  followAuthRedirectGet,
  resolveApiUrl,
} from '../api/client.ts';

export async function login(
  username: string,
  password: string,
): Promise<AccessTokenResponse> {
  return apiPostForm<AccessTokenResponse>('/auth/login', {
    username,
    password,
  });
}

export async function refreshAccessToken(
  init?: Pick<RequestInit, 'signal'>,
): Promise<AccessTokenResponse> {
  return apiPost<AccessTokenResponse>('/auth/refresh', {
    auth: false,
    ...init,
  });
}

export async function logout(): Promise<void> {
  await apiPost<unknown>('/auth/logout', { auth: false });
}

export async function requestEmailVerification(email: string): Promise<void> {
  await apiPost<undefined>('/auth/verifications/email', {
    auth: false,
    body: { email },
  });
}

export async function verifyEmail(token: string): Promise<void> {
  await apiPost<undefined>('/auth/verifications/email/verify', {
    auth: false,
    body: { token },
  });
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiPost<undefined>('/auth/password-resets', {
    auth: false,
    body: { email },
  });
}

export async function confirmPasswordReset(payload: {
  token: string;
  password: string;
  repeat_password: string;
}): Promise<void> {
  await apiPost<undefined>('/auth/password-resets/confirm', {
    auth: false,
    body: payload,
  });
}

export function getOAuthAuthorizeUrl(provider: string): string {
  return resolveApiUrl(`/auth/oauth/${encodeURIComponent(provider)}/authorize`);
}

export async function startOAuthConnect(provider: string): Promise<void> {
  await followAuthRedirectGet(
    `/auth/oauth/${encodeURIComponent(provider)}/authorize/connect`,
  );
}

export async function oauthCallback(
  provider: string,
  params: { code: string; state: string },
): Promise<AccessTokenResponse> {
  return apiGet<AccessTokenResponse>(
    `/auth/oauth/${encodeURIComponent(provider)}/callback`,
    {
      query: params,
      auth: false,
    },
  );
}
