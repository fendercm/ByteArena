"use client";

import { useState } from "react";
import Link from "next/link";
import TournamentCard from "@/components/TournamentCard";

function EmptyState() {
  return (
    <div className="empty-state">
      <h3>Турниров пока нет</h3>
      <p>Станьте первым организатором или загляните позже.</p>
      <Link className="button" href="/tournaments/new">
        Создать турнир
      </Link>
    </div>
  );
}

export default function TournamentList({ tournaments }) {
  const [availableOnly, setAvailableOnly] = useState(false);
  const running = tournaments.filter((t) => t.status === "running");
  const upcoming = tournaments.filter(
    (t) => t.status === "registration" && (!availableOnly || t.teams_count < t.max_teams),
  );
  if (!tournaments.length) return <EmptyState />;
  const countLabel =
    running.length === 1
      ? "турнир"
      : running.length > 1 && running.length < 5
        ? "турнира"
        : "турниров";
  return (
    <div className="tournament-sections">
      <section aria-labelledby="running-title">
        <div className="section-heading">
          <h2 id="running-title">Идут сейчас</h2>
          <span className="badge badge-running">
            {running.length} {countLabel}
          </span>
        </div>
        <div className="tournament-grid running-grid">
          {running.map((t) => (
            <TournamentCard key={t.id} tournament={t} />
          ))}
        </div>
        {!running.length && <p className="muted">Сейчас нет идущих турниров.</p>}
      </section>
      <section aria-labelledby="upcoming-title">
        <div className="section-heading upcoming-heading">
          <h2 id="upcoming-title">Ближайшие</h2>
          <div className="filters" role="group" aria-label="Фильтр ближайших турниров">
            <button
              className={`button button-small ${availableOnly ? "button-secondary" : ""}`}
              aria-pressed={!availableOnly}
              onClick={() => setAvailableOnly(false)}
            >
              Все турниры
            </button>
            <button
              className={`button button-small ${availableOnly ? "" : "button-secondary"}`}
              aria-pressed={availableOnly}
              onClick={() => setAvailableOnly(true)}
            >
              Есть места
            </button>
          </div>
        </div>
        <div className="tournament-grid upcoming-grid">
          {upcoming.map((t) => (
            <TournamentCard key={t.id} tournament={t} />
          ))}
        </div>
        {!upcoming.length && <EmptyState />}
      </section>
    </div>
  );
}
