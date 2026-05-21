import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "../services/api";
import type { User } from "../types/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("festivapro_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then(({ data }) => setUser(data))
      .catch(() => localStorage.removeItem("festivapro_token"))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email: string, password: string) => {
        const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
        localStorage.setItem("festivapro_token", data.access_token);
        const profile = await api.get<User>("/auth/me");
        setUser(profile.data);
      },
      logout: () => {
        localStorage.removeItem("festivapro_token");
        setUser(null);
      }
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
