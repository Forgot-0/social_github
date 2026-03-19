/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the app
 * Access token is stored in memory via tokenManager
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { tokenManager } from '../tokenManager';
import { authApi, usersApi } from '../client';
import type { UserResponse, LoginRequest } from '../types';
import { toast } from 'sonner';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const isAuthenticated = tokenManager.isAuthenticated() && user !== null;

  /**
   * Load user data on mount if access token exists
   */
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (tokenManager.isAuthenticated()) {
          const userData = await usersApi.getMe();
          setUser(userData);
        }
      } catch (error) {
        // If getMe fails, try to refresh
        try {
          const response = await authApi.refresh();
          tokenManager.setAccessToken(response.access_token);
          const userData = await usersApi.getMe();
          setUser(userData);
        } catch (refreshError) {
          // Both failed, clear token
          tokenManager.clearAccessToken();
          setUser(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  /**
   * Login user
   */
  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials);
      
      // Store access token in MEMORY
      tokenManager.setAccessToken(response.access_token);
      
      // Fetch user data
      const userData = await usersApi.getMe();
      setUser(userData);
      
      toast.success('Вход выполнен успешно!');
      navigate('/');
    } catch (error: any) {
      tokenManager.clearAccessToken();
      setUser(null);
      
      if (error?.response?.data?.error?.code === 'WRONG_LOGIN_DATA') {
        toast.error('Неверный логин или пароль');
      } else {
        toast.error('Ошибка входа', {
          description: 'Попробуйте позже',
        });
      }
      throw error;
    }
  };

  /**
   * Logout user
   */
  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear access token from memory
      tokenManager.clearAccessToken();
      setUser(null);
      
      toast.success('Вы вышли из системы');
      navigate('/login');
    }
  };

  /**
   * Refresh user data
   */
  const refreshUser = async () => {
    if (tokenManager.isAuthenticated()) {
      try {
        const userData = await usersApi.getMe();
        setUser(userData);
      } catch (error) {
        console.error('Failed to refresh user:', error);
      }
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
