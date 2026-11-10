"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { usePathname, useRouter } from "next/navigation";
import { loginReturnKey } from "./TournamentLoginLink";

const AuthContext = createContext(null);

export default function AuthProvider({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setUser(await api.getMe());
    } catch (err) {
      setUser(null);
      if (err.status !== 401) setError("Не удалось проверить вход. Попробуйте ещё раз.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Текущий OAuth callback возвращает на главную и не принимает параметр next.
  // Восстанавливаем только известный маршрут формы в этой же вкладке.
  useEffect(() => {
    if (loading || error) return;
    try {
      const expires = Number(sessionStorage.getItem(loginReturnKey));
      sessionStorage.removeItem(loginReturnKey);
      if (user && pathname === "/" && expires > Date.now()) {
        router.replace("/tournaments/new");
      }
    } catch {
      // Запрет sessionStorage не мешает авторизации.
    }
  }, [user, loading, error, pathname, router]);

  async function logout() {
    await api.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
