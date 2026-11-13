"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { discordLoginUrl, getCurrentUser, signOut } from "@/lib/auth";

const buttonClass = "button button-secondary button-small";

export default function HeaderAccount() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [leaving, setLeaving] = useState(false);
  const [error, setError] = useState("");
  const [failedAvatar, setFailedAvatar] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");

    async function loadAccount() {
      try {
        const account = await getCurrentUser(controller.signal);
        if (!controller.signal.aborted) setUser(account);
      } catch {
        if (!controller.signal.aborted) setError("Не удалось проверить вход");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadAccount();
    return () => controller.abort();
  }, [attempt]);

  async function handleLogout() {
    setLeaving(true);
    setError("");
    try {
      await signOut();
      setUser(null);
    } catch {
      setError("Не удалось выйти. Попробуй ещё раз.");
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
      {error && (
        <p className="header-account-error" role="status">
          {error}
          {!user && (
            <button
              type="button"
              className={buttonClass}
              onClick={() => setAttempt((value) => value + 1)}
            >
              Повторить
            </button>
          )}
        </p>
      )}
    </div>
  );
}
