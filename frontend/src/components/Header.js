"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "./AuthProvider";

export default function Header() {
  const { user, loading, error, logout } = useAuth();
  const [pending, setPending] = useState(false);
  const [logoutError, setLogoutError] = useState("");

  async function handleLogout() {
    setPending(true);
    setLogoutError("");
    try {
      await logout();
    } catch {
      setLogoutError("Не удалось выйти. Повторите попытку.");
    } finally {
      setPending(false);
    }
  }

  return (
    <header className="site-header">
      <nav className="container header-content" aria-label="Основная навигация">
        <Link href="/" className="brand">
          <span className="brand-icon">B</span>ByteArena
        </Link>
        <Link href="/">Турниры</Link>
        <Link href="/tournaments/new">Создать турнир</Link>
        <div className="header-account">
          {loading ? (
            <span className="muted">Проверяем вход…</span>
          ) : user ? (
            <>
              <span className="avatar" aria-hidden="true">
                {user.nickname.slice(0, 1)}
              </span>
              <span>{user.nickname}</span>
              <button className="button secondary small" onClick={handleLogout} disabled={pending}>
                {pending ? "Выходим…" : "Выйти"}
              </button>
            </>
          ) : (
            !error && (
              <a className="button secondary small" href="/api/auth/discord/login">
                Войти через Discord
              </a>
            )
          )}
        </div>
      </nav>
      {logoutError && (
        <p className="container error-message" role="alert">
          {logoutError}
        </p>
      )}
    </header>
  );
}
