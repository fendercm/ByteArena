"use client";

import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { discordLoginUrl } from "@/lib/auth";

export default function MyTeamLink() {
  const { user, loading } = useAuth();

  // Пока проверяем вход, ссылка никуда не ведёт, чтобы не запустить вход повторно.
  if (loading) return <a aria-disabled="true">Моя команда</a>;

  // /me отдаёт команду игрока; без команды ведём в профиль, там видно «Команда не указана».
  if (user) {
    const href = user.team ? `/teams/${user.team.id}` : `/users/${user.id}`;
    return <Link href={href}>Моя команда</Link>;
  }

  // Адрес бэка, а не страница Next: обычная ссылка, без prefetch через Link.
  return <a href={discordLoginUrl}>Моя команда</a>;
}
