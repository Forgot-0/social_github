export const OAUTH_PROVIDERS = ['google', 'yandex', 'github'] as const;
export type OAuthProvider = (typeof OAUTH_PROVIDERS)[number];
