import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

export interface User {
  id: number;
  email: string;
  created_at: string;
  last_login_at: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = async () => {
    try {
      const data = await authApi.getCurrentSession();
      if (data.authenticated && data.user) {
        setUser(data.user);
      } else {
        setUser(null);
        localStorage.removeItem('qoneqt_token');
      }
    } catch (err) {
      console.warn('Session check failed or unauthenticated:', err);
      setUser(null);
      localStorage.removeItem('qoneqt_token');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshSession();
  }, []);

  const login = (token: string, userData: User) => {
    localStorage.setItem('qoneqt_token', token);
    setUser(userData);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('qoneqt_token');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
