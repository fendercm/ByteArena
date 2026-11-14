"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { discordLoginUrl } from "@/lib/auth";

import { useAuth } from "@/components/AuthProvider";

const buttonClass = "button button-secondary button-small";

export default function HeaderAccount() {
  const { user, loading, error, refresh, logout } = useAuth();
  const [leaving, setLeaving] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [failedAvatar, setFailedAvatar] = useState(null);

  async function handleLogout() {
    setLeaving(true);
    setLogoutError("");
    try {
      await logout();
    } catch {
      setLogoutError("Не удалось выйти. Попробуй ещё раз.");
    } finally {
      setLeaving(false);
    }
  }

  if (loading)
    return (
      <span className="muted" role="status">
        Проверяем вход…
      </span>
    );

  return (
    <div className="header-account">
      {user ? (
        <div className="header-account-controls">
          <Link href={`/users/${user.id}`} className="header-profile">
            <span className="header-avatar" aria-hidden="true">
              {user.avatar_url && user.avatar_url !== failedAvatar ? (
                <Image
                  src={user.avatar_url}
                  alt=""
                  width={24}
                  height={24}
                  unoptimized
                  onError={() => setFailedAvatar(user.avatar_url)}
                />
              ) : (
                Array.from(user.nickname)[0]?.toUpperCase() || "?"
              )}
            </span>
            <span className="header-nickname">{user.nickname}</span>
          </Link>
          <button type="button" className={buttonClass} onClick={handleLogout} disabled={leaving}>
            {leaving ? "Выходим…" : "Выйти"}
          </button>
        </div>
      ) : (
        <a className={buttonClass} href={discordLoginUrl}>
          Войти через Discord
        </a>
      )}
      {(error || logoutError) && (
        <p className="header-account-error" role="status">
          {error || logoutError}
          {!user && (
            <button
              type="button"
              className={buttonClass}
              onClick={refresh}
            >
              Повторить
            </button>
          )}
        </p>
      )}
    </div>
  );
}
