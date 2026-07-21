import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api, getStoredToken, setStoredToken, UNAUTHORIZED_EVENT } from "@/lib/api-client";
import { decodeJwtPayload, isJwtExpired } from "@/lib/jwt";

interface AuthContextValue {
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function usernameFromToken(token: string | null): string | null {
  if (!token || isJwtExpired(token)) return null;
  return decodeJwtPayload(token)?.sub ?? null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(() => usernameFromToken(getStoredToken()));

  const logout = useCallback(() => {
    setStoredToken(null);
    setUsername(null);
  }, []);

  const login = useCallback(async (usernameInput: string, password: string) => {
    const { access_token } = await api.login(usernameInput, password);
    setStoredToken(access_token);
    setUsername(usernameFromToken(access_token));
  }, []);

  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const value = useMemo(
    () => ({ username, isAuthenticated: username !== null, login, logout }),
    [username, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
