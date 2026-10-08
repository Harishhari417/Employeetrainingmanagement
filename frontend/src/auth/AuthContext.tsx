
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../services/api";
import type { Role } from "../types";

export interface AuthUser {
  id: string;
  username: string;
  name: string;
  role: Role;
  employeeId?: string | null;
  department?: string | null;
}

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("auth_user");
  localStorage.removeItem("token_expires_at");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem("auth_user");
    const expiry = Number(localStorage.getItem("token_expires_at") || 0);
    if (expiry && expiry <= Date.now()) {
      clearSession();
      return null;
    }
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      clearSession();
      return null;
    }
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const expiry = Number(localStorage.getItem("token_expires_at") || 0);
    if (!expiry) return;
    const remaining = expiry - Date.now();
    if (remaining <= 0) {
      clearSession();
      setUser(null);
      return;
    }
    const timer = window.setTimeout(() => {
      clearSession();
      setUser(null);
      window.location.href = "/login";
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [user]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    async login(username, password) {
      const res = await api.post<{accessToken:string;expiresIn:number;user:AuthUser}>("/auth/login", { username, password });
      localStorage.setItem("access_token", res.data.accessToken);
      localStorage.setItem("auth_user", JSON.stringify(res.data.user));
      localStorage.setItem("token_expires_at", String(Date.now() + (res.data.expiresIn || 7200) * 1000));
      setUser(res.data.user);
    },
    logout() {
      clearSession();
      setUser(null);
      window.location.href = "/login";
    },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
