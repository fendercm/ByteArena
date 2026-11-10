"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";

export default function HeaderAccount() {
  const { user, loading, error, refresh, logout } = useAuth();
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

  if (loading)
    return (
      <span className="muted" role="status">
        Проверяем вход…
      </span>
    );
  if (error)
    return (
      <button className="button button-secondary button-small" onClick={refresh}>
        Повторить проверку входа
      </button>
    );
  if (!user)
    return (
      <a className="button button-secondary button-small" href="/api/auth/discord/login">
        Войти
      </a>
    );

  return (
    <div className="header-account">
      <Link href={`/users/${user.id}`} className="account-profile">
        <span className="account-avatar" aria-hidden="true">
          {user.nickname.slice(0, 1)}
        </span>
        <span>{user.nickname}</span>
      </Link>
      <button
        className="button button-secondary button-small"
        onClick={handleLogout}
        disabled={pending}
      >
        {pending ? "Выходим…" : "Выйти"}
      </button>
      {logoutError && (
        <span className="account-error" role="alert">
          {logoutError}
        </span>
      )}
    </div>
  );
}
