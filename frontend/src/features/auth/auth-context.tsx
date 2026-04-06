import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { UserResponse } from '../../types/api/user.ts';
import { configureApiClient } from '../../services/api/client.ts';
import {
  getOAuthAuthorizeUrl,
  getOAuthConnectUrl,
  login as apiLogin,
  logout as apiLogout,
  oauthCallback,
  refreshAccessToken,
} from '../../services/auth/auth.service.ts';
import {
  getCurrentUser,
  registerUser,
} from '../../services/users/users.service.ts';
import type { RegisterUserBody } from '../../services/users/users.service.ts';
import type { OAuthProvider } from './oauth-providers.ts';

type AuthContextValue = {
  isReady: boolean;
  isAuthenticated: boolean;
  user: UserResponse | null;
  login: (username: string, password: string) => Promise<void>;
  register: (body: RegisterUserBody) => Promise<void>;
  logout: () => Promise<void>;
  /** Редирект на провайдера; refresh_token придёт в httpOnly cookie (SameSite=strict, Secure). */
  startOAuthLogin: (provider: OAuthProvider) => Promise<void>;
  /** OAuth connect для привязки внешнего аккаунта к текущему пользователю. */
  startOAuthConnect: (provider: OAuthProvider) => Promise<void>;
  completeOAuthLogin: (
    provider: OAuthProvider,
    params: { code: string; state: string },
  ) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/** Access token только в памяти процесса; refresh — cookie `refresh_token` на стороне бэкенда. */
const accessTokenRef = { current: null as string | null };

function setAccessToken(token: string | null): void {
  accessTokenRef.current = token;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const applySession = useCallback(async (accessToken: string) => {
    setAccessToken(accessToken);
    const me = await getCurrentUser();
    setUser(me);
    setIsAuthenticated(true);
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  useEffect(() => {
    configureApiClient({
      getAccessToken: () => accessTokenRef.current,
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const refreshTimeoutMs = 15_000;
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      refreshTimeoutMs,
    );

    (async () => {
      try {
        const { access_token } = await refreshAccessToken({
          signal: controller.signal,
        });
        if (cancelled) return;
        await applySession(access_token);
      } catch {
        if (!cancelled) clearSession();
      } finally {
        window.clearTimeout(timeoutId);
        if (!cancelled) setIsReady(true);
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [applySession, clearSession]);

  const login = useCallback(
    async (username: string, password: string) => {
      const { access_token } = await apiLogin(username, password);
      await applySession(access_token);
    },
    [applySession],
  );

  const register = useCallback(async (body: RegisterUserBody) => {
    await registerUser(body);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const startOAuthLogin = useCallback(async (provider: OAuthProvider) => {
    const { url } = await getOAuthAuthorizeUrl(provider);
    window.location.assign(url);
  }, []);

  const startOAuthConnect = useCallback(async (provider: OAuthProvider) => {
    const { url } = await getOAuthConnectUrl(provider);
    window.location.assign(url);
  }, []);

  const completeOAuthLogin = useCallback(
    async (
      provider: OAuthProvider,
      params: { code: string; state: string },
    ) => {
      const { access_token } = await oauthCallback(provider, params);
      await applySession(access_token);
    },
    [applySession],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      isAuthenticated,
      user,
      login,
      register,
      logout,
      startOAuthLogin,
      startOAuthConnect,
      completeOAuthLogin,
    }),
    [
      isReady,
      isAuthenticated,
      user,
      login,
      register,
      logout,
      startOAuthLogin,
      startOAuthConnect,
      completeOAuthLogin,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook рядом с провайдером; fast refresh предупреждает о не-компонентных экспортах.
// eslint-disable-next-line react-refresh/only-export-components -- useAuth привязан к AuthProvider
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
