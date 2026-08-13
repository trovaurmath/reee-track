import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { loginRequest, logoutRequest, refreshRequest } from "../../services/api";
import type { User } from "../../types/auth";

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    refreshRequest()
      .then((response) => {
        setUser(response.user);
        setAccessToken(response.access_token);
        setExpiresAt(Date.now() + response.expires_in * 1000);
      })
      .catch(() => {
        setUser(null);
        setAccessToken(null);
        setExpiresAt(null);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!expiresAt) return undefined;
    const delay = Math.max(expiresAt - Date.now() - 60_000, 1_000);
    const timer = window.setTimeout(() => {
      refreshRequest()
        .then((response) => {
          setUser(response.user);
          setAccessToken(response.access_token);
          setExpiresAt(Date.now() + response.expires_in * 1000);
        })
        .catch(() => {
          setUser(null);
          setAccessToken(null);
          setExpiresAt(null);
        });
    }, delay);
    return () => window.clearTimeout(timer);
  }, [expiresAt]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      loading,
      login: async (username, password) => {
        const response = await loginRequest(username, password);
        setUser(response.user);
        setAccessToken(response.access_token);
        setExpiresAt(Date.now() + response.expires_in * 1000);
      },
      logout: async () => {
        await logoutRequest();
        setUser(null);
        setAccessToken(null);
        setExpiresAt(null);
      },
    }),
    [accessToken, loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return context;
}
