import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMeQuery } from '../../api/hooks/useUsers';
import { useLoginMutation, useLogoutMutation } from '../../api/hooks/useAuth';
import { tokenManager } from '../../api/tokenManager';
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
  
  const { data: user, isLoading: userLoading, refetch } = useMeQuery({
    enabled: isInitialized && !!tokenManager.getAccessToken(),
    retry: false,
  });

  const loginMutation = useLoginMutation();
  const logoutMutation = useLogoutMutation();

  useEffect(() => {
    setIsInitialized(true);
  }, []);

  const login = async (username: string, password: string) => {
    await loginMutation.mutateAsync({ username, password });
    await refetch();
  };

  const logout = async () => {
    await logoutMutation.mutateAsync();
    tokenManager.clearTokens();
    queryClient.clear();
  };

  const isAuthenticated = !!user && !!tokenManager.getAccessToken();
  const isLoading = !isInitialized || userLoading;

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
