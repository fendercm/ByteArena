"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import TournamentLink from "@/components/TournamentLink";
import { api, formatDate } from "@/lib/api";
import "../tournaments.css";

const statuses = {
  draft: "Черновик",
  registration: "Регистрация",
  running: "Идёт",
  finished: "Завершён",
};

export default function TournamentPage({ params }) {
  const [tournament, setTournament] = useState(null);
  const [error, setError] = useState("");
  const [created, setCreated] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    setCreated(new URLSearchParams(window.location.search).get("created") === "1");
    const controller = new AbortController();
    setError("");
    setTournament(null);
    api
      .getTournament(params.id, controller.signal)
      .then(setTournament)
      .catch((err) => {
        if (err.name !== "AbortError")
          setError(err.status === 404 ? "Турнир не найден" : "Не удалось загрузить турнир");
      });
    return () => controller.abort();
  }, [params.id, attempt]);

  if (error)
    return (
      <section className="tournament-page page-stack">
        <h1>{error}</h1>
        <button className="button" onClick={() => setAttempt((n) => n + 1)}>
          Повторить
        </button>
        <Link href="/">Все турниры</Link>
      </section>
    );
  if (!tournament) return <p role="status">Загружаем турнир…</p>;

  return (
    <section className="tournament-page page-stack">
      <Link className="back-link" href="/">
        ← Все турниры
      </Link>
      {created && (
        <p className="success-notice" role="status">
          Турнир создан. Поделитесь ссылкой с участниками.
        </p>
      )}
      <div className="title-row">
        <h1>{tournament.title}</h1>
        <span className={`badge badge-${tournament.status}`}>{statuses[tournament.status]}</span>
      </div>
      <div className="panel tournament-meta">
        <div>
          <span className="muted">Начало · МСК</span>
          <p>{formatDate(tournament.starts_at)}</p>
        </div>
        <div>
          <span className="muted">Команды</span>
          <p>
            {tournament.teams_count} / {tournament.max_teams}
          </p>
        </div>
        <div>
          <span className="muted">Игра</span>
          <p>Counter-Strike 2</p>
        </div>
      </div>
      {tournament.description && (
        <div className="panel">
          <h2>О турнире</h2>
          <p className="preserve-lines">{tournament.description}</p>
        </div>
      )}
      <div className="panel">
        <h2>Правила</h2>
        <p className="preserve-lines muted">
          {tournament.rules || "Организатор пока не добавил правила."}
        </p>
      </div>
      <div className="panel">
        <TournamentLink id={tournament.id} />
      </div>
    </section>
  );
}
