import type { IHttpClient } from '../application/ports/http-client.port';
import type { AccessTokenResponse } from '../domain/types/api.types';

export function oauthAuthorizeUrl(
  apiBasePath: string,
  provider: string,
): string {
  const b = apiBasePath.endsWith('/') ? apiBasePath.slice(0, -1) : apiBasePath;
  return `${b}/auth/oauth/${encodeURIComponent(provider)}/authorize`;
}

export function oauthConnectUrl(apiBasePath: string, provider: string): string {
  const b = apiBasePath.endsWith('/') ? apiBasePath.slice(0, -1) : apiBasePath;
  return `${b}/auth/oauth/${encodeURIComponent(provider)}/authorize/connect`;
}

export class AuthService {
  constructor(private readonly http: IHttpClient) {}

  login(username: string, password: string): Promise<AccessTokenResponse> {
    const formUrlEncoded = new URLSearchParams();
    formUrlEncoded.set('username', username);
    formUrlEncoded.set('password', password);
    return this.http.request<AccessTokenResponse>({
      path: '/auth/login',
      method: 'POST',
      formUrlEncoded,
    });
  }

  refresh(): Promise<AccessTokenResponse> {
    return this.http.request<AccessTokenResponse>({
      path: '/auth/refresh',
      method: 'POST',
    });
  }

  logout(): Promise<void> {
    return this.http.request<void>({
      path: '/auth/logout',
      method: 'POST',
      parseAs: 'void',
    });
  }

  requestEmailVerification(email: string): Promise<void> {
    return this.http.request<void>({
      path: '/auth/verifications/email',
      method: 'POST',
      jsonBody: { email },
      parseAs: 'void',
    });
  }

  verifyEmail(token: string): Promise<void> {
    return this.http.request<void>({
      path: '/auth/verifications/email/verify',
      method: 'POST',
      jsonBody: { token },
      parseAs: 'void',
    });
  }

  requestPasswordReset(email: string): Promise<void> {
    return this.http.request<void>({
      path: '/auth/password-resets',
      method: 'POST',
      jsonBody: { email },
      parseAs: 'void',
    });
  }

  confirmPasswordReset(body: {
    token: string;
    password: string;
    repeat_password: string;
  }): Promise<void> {
    return this.http.request<void>({
      path: '/auth/password-resets/confirm',
      method: 'POST',
      jsonBody: body,
      parseAs: 'void',
    });
  }

  oauthCallback(
    provider: string,
    query: { code: string; state: string },
  ): Promise<AccessTokenResponse> {
    return this.http.request<AccessTokenResponse>({
      path: `/auth/oauth/${encodeURIComponent(provider)}/callback`,
      method: 'GET',
      query: { code: query.code, state: query.state },
    });
  }
}
