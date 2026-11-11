"use client";

import { useEffect, useState } from "react";
import { getTournaments } from "@/lib/api";
import TournamentList from "@/components/TournamentList";

export default function HomeTournaments() {
  const [tournaments, setTournaments] = useState([]);
  const [state, setState] = useState("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState("loading");
    async function load() {
      try {
        const [running, upcoming] = await Promise.all([
          getTournaments("running", controller.signal),
          getTournaments("registration", controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setTournaments([...running.items, ...upcoming.items]);
        setState("ready");
      } catch {
        if (!controller.signal.aborted) setState("error");
      }
    }
    load();
    return () => controller.abort();
  }, [attempt]);

  if (state === "loading") {
    return (
      <section className="tournament-sections" aria-label="Турниры" aria-busy="true">
        <p className="muted" role="status">
          Загружаем турниры…
        </p>
        <div className="tournament-grid upcoming-grid" aria-hidden="true">
          {[1, 2, 3].map((id) => (
            <div className="tournament-skeleton" key={id}>
              <span />
              <span />
              <span />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (state === "error") {
    return (
      <section className="empty-state tournament-sections" role="alert">
        <h2>Не удалось загрузить турниры</h2>
        <p>Проверьте подключение к интернету и попробуйте ещё раз.</p>
        <div>
          <button className="button" onClick={() => setAttempt((value) => value + 1)}>
            Повторить
          </button>
        </div>
      </section>
    );
  }

  return (
    <div className="tournament-sections">
      <TournamentList tournaments={tournaments} />
    </div>
  );
}
