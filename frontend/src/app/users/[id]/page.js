"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { getUserProfile } from "@/lib/api";

export default function UserPage({ params }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setLoading(true);
      setNotFound(false);
      setError(false);
      setUser(null);

      try {
        const data = await getUserProfile(params.id);

        if (!cancelled) setUser(data);
      } catch (err) {
        console.error("Profile loading error:", err);

        if (!cancelled) {
          if (err.status === 404) {
            setNotFound(true);
          } else {
            setError(true);
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, [params.id]);

  if (loading) {
    return (
      <section>
        <p>Загрузка профиля...</p>
      </section>
    );
  }

  if (notFound) {
    return (
      <section>
        <h1>Игрок не найден</h1>
      </section>
    );
  }

  if (error || !user) {
    return (
      <section>
        <h1>Не удалось загрузить профиль</h1>
        <p>Попробуйте обновить страницу позже.</p>
      </section>
    );
  }

  const firstLetter = user.nickname?.trim().charAt(0).toUpperCase() || "?";

  return (
    <section>
      <div className="user-profile">
        {user.avatar_url ? (
          <Image
            src={user.avatar_url}
            alt={`Аватар ${user.nickname}`}
            width={120}
            height={120}
            unoptimized
            style={{
              borderRadius: "50%",
              objectFit: "cover",
            }}
          />
        ) : (
          <div
            style={{
              width: "120px",
              height: "120px",
              borderRadius: "50%",
              background: "#333",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "48px",
            }}
          >
            {firstLetter}
          </div>
        )}

        <h1>{user.nickname}</h1>
        <p>ID игрока: {user.id}</p>
      </div>

      <div>
        <h2>Команда</h2>
        {user.team ? (
          <p>
            <Link href={`/teams/${user.team.id}`}>{user.team.name}</Link>
          </p>
        ) : (
          <p>Команда не указана</p>
        )}
      </div>

      <div>
        <h2>Турниры</h2>
        {user.tournaments?.length > 0 ? (
          <ul>
            {user.tournaments.map((tournament) => {
              const result = tournament.result === "champion"
                ? "Чемпион"
                : tournament.result === "eliminated"
                  ? tournament.eliminated_round
                    ? `Выбыли в раунде ${tournament.eliminated_round}`
                    : "Выбыли"
                  : tournament.result === "running" ? "Идёт" : null;
              return (
                <li key={tournament.id}>
                  <span>{tournament.title}</span>
                  {result && <span> — {result}</span>}
                </li>
              );
            })}
          </ul>
        ) : (
          <p>Пока нет турниров</p>
        )}
      </div>
    </section>
  );
}
