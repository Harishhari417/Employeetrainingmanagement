import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem("auth_user");

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw);
    } catch {
      localStorage.removeItem("auth_user");
      return null;
    }
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setLoading(false);
      return;
    }

    api
      .get<AuthUser>("/api/auth/me")
      .then((res) => {
        setUser(res.data);
        localStorage.setItem(
          "auth_user",
          JSON.stringify(res.data),
        );
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,

      async login(username, password) {
        const res = await api.post<{
          accessToken: string;
          user: AuthUser;
        }>("/api/auth/login", {
          username,
          password,
        });

        localStorage.setItem(
          "access_token",
          res.data.accessToken,
        );

        localStorage.setItem(
          "auth_user",
          JSON.stringify(res.data.user),
        );

        setUser(res.data.user);
      },

      logout() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        setUser(null);
      },
    }),
    [user, loading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}