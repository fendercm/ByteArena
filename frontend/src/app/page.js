"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, formatDate } from "@/lib/api";

export default function HomePage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    api
      .getTournaments(controller.signal)
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError("Не удалось загрузить турниры.");
      });
    return () => controller.abort();
  }, [attempt]);
  const groups = [
    { title: "Идут сейчас", items: data?.items.filter((item) => item.status === "running") ?? [] },
    {
      title: "Ближайшие",
      items: data?.items.filter((item) => item.status === "registration") ?? [],
    },
  ];
  return (
    <section className="page-stack">
      <div className="title-row">
        <h1>Турниры CS2</h1>
        <Link className="button" href="/tournaments/new">
          Создать турнир
        </Link>
      </div>
      {error ? (
        <div className="compact-panel panel" role="alert">
          <p>{error}</p>
          <button className="button secondary" onClick={() => setAttempt((n) => n + 1)}>
            Повторить
          </button>
        </div>
      ) : !data ? (
        <p role="status">Загружаем турниры…</p>
      ) : (
        groups.map((group) => (
          <section className="page-stack" key={group.title}>
            <h2>{group.title}</h2>
            {group.items.length === 0 ? (
              <p className="muted">Турниров пока нет.</p>
            ) : (
              <div className="tournament-grid">
                {group.items.map((item) => (
                  <Link
                    key={item.id}
                    className="panel tournament-card"
                    href={`/tournaments/${item.id}`}
                  >
                    <span className="badge">
                      {item.status === "running" ? "Идёт" : "Регистрация"}
                    </span>
                    <h2>{item.title}</h2>
                    <p className="muted">{formatDate(item.starts_at)} МСК</p>
                    <p>
                      {item.teams_count} / {item.max_teams} команд
                    </p>
                  </Link>
                ))}
              </div>
            )}
          </section>
        ))
      )}
    </section>
  );
}
