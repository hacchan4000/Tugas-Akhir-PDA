'use client';

import React, { createContext, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { showToast } from '@/app/components/atoms/toast';
import { User } from '@/model/User';
import { AuthService } from '@/services/api/auth.service';
import { getErrorMessage } from '@/utils/handleError';

interface AuthContextProps {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User | null>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

export const AuthContext = createContext<AuthContextProps>({
  user: null,
  loading: true,
  isAuthenticated: false,
  login: async () => null,
  logout: async () => {},
  refreshUser: async () => null,
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  const refreshUser = useCallback(async (): Promise<User | null> => {
    try {
      const currentUser = await AuthService.me();
      setUser(currentUser);
      return currentUser;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    AuthService.me()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<User | null> => {
      try {
        const loggedInUser = await AuthService.login(email, password);
        setUser(loggedInUser);
        showToast(`Selamat datang, ${loggedInUser.name}`, 'success');
        router.push('/');
        return loggedInUser;
      } catch (error) {
        const message = getErrorMessage(error);
        showToast(message, 'error');
        return null;
      }
    },
    [router]
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await AuthService.logout();
    } catch {
      // Abaikan jika sesi sudah kedaluwarsa di server
    } finally {
      setUser(null);
      showToast('Sesi operator berakhir', 'info');
      router.push('/login');
    }
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: Boolean(user),
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
