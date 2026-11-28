"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import TournamentMatches from "@/components/TournamentMatches";
import TournamentLink from "@/components/TournamentLink";
import TournamentRegistration from "@/components/TournamentRegistration";
import TournamentTeams from "@/components/TournamentTeams";
import { api, formatDate } from "@/lib/api";
import { getChampion } from "@/lib/bracket";
import "../tournaments.css";

const statuses = {
  draft: "Черновик",
  registration: "Регистрация",
  closed: "Регистрация закрыта",
  running: "Идёт",
  finished: "Завершён",
};

export default function TournamentPage({ params }) {
  const { id } = use(params);
  const [tournament, setTournament] = useState(null);
  const [error, setError] = useState("");
  const [created, setCreated] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    setCreated(new URLSearchParams(window.location.search).get("created") === "1");
    const controller = new AbortController();
    setError("");
    setTournament(null);
    let inFlight = false;
    let currentStatus;
    async function loadTournament() {
      if (inFlight) return;
      inFlight = true;
      try {
        const data = await api.getTournament(id, controller.signal);
        if (controller.signal.aborted) return;
        currentStatus = data.status;
        setTournament(data);
        setError("");
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.status === 404 ? "Турнир не найден" : "Не удалось обновить турнир");
        }
      } finally {
        inFlight = false;
      }
    }
    function refreshVisibleTournament() {
      if (document.visibilityState === "visible") loadTournament();
    }
    loadTournament();
    const timer = setInterval(() => {
      if (currentStatus === "running") refreshVisibleTournament();
    }, 15000);
    window.addEventListener("focus", refreshVisibleTournament);
    document.addEventListener("visibilitychange", refreshVisibleTournament);
    return () => {
      controller.abort();
      clearInterval(timer);
      window.removeEventListener("focus", refreshVisibleTournament);
      document.removeEventListener("visibilitychange", refreshVisibleTournament);
    };
  }, [id, attempt]);

  if (error && !tournament)
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
  const champion = getChampion(tournament);

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
      {error && (
        <div className="error-message" role="alert">
          <p>{error}. Показаны последние загруженные данные.</p>
          <button className="button button-secondary" onClick={() => setAttempt((n) => n + 1)}>
            Повторить
          </button>
        </div>
      )}
      {champion && (
        <section className="panel tournament-champion" aria-labelledby="champion-heading">
          <h2 id="champion-heading">Чемпион</h2>
          <Link href={`/teams/${champion.id}`}>{champion.name}</Link>
        </section>
      )}
      <div className="panel tournament-meta">
        <div>
          <span className="muted">Начало · МСК</span>
          <p>{formatDate(tournament.starts_at)}</p>
        </div>
        <div>
          <span className="muted">Команды</span>
          <p>
            {tournament.teams_count} из {tournament.max_teams}
          </p>
        </div>
        <div>
          <span className="muted">Игра</span>
          <p>Counter-Strike 2</p>
        </div>
      </div>
      <TournamentRegistration key={tournament.id} tournament={tournament} />
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
        <TournamentTeams key={tournament.id} tournament={tournament} />
      </div>

      <div className="panel">
        <h2>Турнирная сетка</h2>
        <TournamentMatches tournament={tournament} />
      </div>
      <div className="panel">
        <TournamentLink id={tournament.id} />
      </div>
    </section>
  );
}
