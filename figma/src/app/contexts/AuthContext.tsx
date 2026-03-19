import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMeQuery } from '../../api/hooks/useUsers';
import { useLoginMutation, useLogoutMutation } from '../../api/hooks/useAuth';
import { tokenManager } from '../../api/tokenManager';
import { authApi } from '../../api/client';
import { UserResponse } from '../../api/types';
import { useQueryClient } from '@tanstack/react-query';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isInitialized, setIsInitialized] = useState(false);
  const [hasTriedRefresh, setHasTriedRefresh] = useState(false);
  
  // Попытка получить access token через refresh при загрузке
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Попробуем обновить токен через refresh endpoint
        // Это сработает только если у пользователя есть валидный refresh token в cookie
        const response = await authApi.refresh();
        tokenManager.setAccessToken(response.access_token);
      } catch (error) {
        // Если refresh не удался (нет cookie или истек), просто продолжаем без токена
        tokenManager.clearAccessToken();
      } finally {
        setHasTriedRefresh(true);
        setIsInitialized(true);
      }
    };

    // Небольшая задержка чтобы убедиться что все провайдеры инициализированы
    const timer = setTimeout(() => {
      initAuth();
    }, 0);

    return () => clearTimeout(timer);
  }, []);

  const { data: user, isLoading: userLoading, refetch } = useMeQuery({
    enabled: isInitialized && hasTriedRefresh && !!tokenManager.getAccessToken(),
    retry: false,
  });

  const loginMutation = useLoginMutation();
  const logoutMutation = useLogoutMutation();

  const login = async (username: string, password: string) => {
    await loginMutation.mutateAsync({ username, password });
    await refetch();
  };

  const logout = async () => {
    await logoutMutation.mutateAsync();
    tokenManager.clearAccessToken();
    queryClient.clear();
  };

  const isAuthenticated = !!user && !!tokenManager.getAccessToken();
  const isLoading = !isInitialized || !hasTriedRefresh || userLoading;

  // Показываем загрузку во время инициализации
  if (!isInitialized || !hasTriedRefresh) {
    return (
      <AuthContext.Provider value={{ user: null, isLoading: true, isAuthenticated: false, login, logout }}>
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
            <p className="mt-4 text-sm text-muted-foreground">Загрузка...</p>
          </div>
        </div>
      </AuthContext.Provider>
    );
  }

  return (
    <AuthContext.Provider value={{ user: user || null, isLoading, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}