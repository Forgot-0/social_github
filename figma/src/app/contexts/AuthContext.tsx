import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../lib/api';
import { toast } from 'sonner';

interface User {
  id: number;
  username: string;
  email: string;
  is_verified?: boolean;
  is_active?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; email: string; password: string; repeat_password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        const restored = await api.restoreSession();
        if (!restored) {
          setUser(null);
          return;
        }
        const userData = await api.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to bootstrap auth:', error);
        api.resetAuth();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    void bootstrapAuth();
  }, []);

  const refreshUser = async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch (error: any) {
      console.error('Failed to fetch user:', error);
      api.resetAuth();
      setUser(null);
      throw error;
    }
  };

  const login = async (username: string, password: string) => {
    try {
      await api.login(username, password);
      await refreshUser();
      toast.success('Вход выполнен успешно!');
    } catch (error: any) {
      console.error('Login error:', error);
      const message = error.error?.message || 'Ошибка входа';
      toast.error(message);
      throw error;
    }
  };

  const register = async (data: { username: string; email: string; password: string; repeat_password: string }) => {
    try {
      await api.register(data);
      toast.success('Регистрация успешна! Теперь войдите в систему.');
    } catch (error: any) {
      console.error('Registration error:', error);
      const message = error.error?.message || 'Ошибка регистрации';
      toast.error(message);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.logout();
      setUser(null);
      toast.success('Вы вышли из системы');
    } catch (error: any) {
      console.error('Logout error:', error);
      toast.error('Ошибка при выходе');
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
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
