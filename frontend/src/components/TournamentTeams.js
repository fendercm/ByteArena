"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function TournamentTeams({ tournament }) {
  const confirmed = tournament.teams.filter((team) => team.status === "approved");
  const [rosters, setRosters] = useState(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const tournamentId = tournament.id;
  const hasTeams = confirmed.length > 0;

  useEffect(() => {
    if (!hasTeams) return;
    const controller = new AbortController();
    api.getTournamentTeams(tournamentId, controller.signal).then(
      ({ items }) => {
        if (!controller.signal.aborted) setRosters(items);
      },
      () => {
        if (!controller.signal.aborted) setError(true);
      },
    );
    return () => controller.abort();
  }, [attempt, hasTeams, tournamentId]);

  return (
    <section aria-labelledby="confirmed-teams">
      <h2 id="confirmed-teams">Подтверждённые команды</h2>
      {error ? (
        <>
          <p className="error-message" role="alert">
            Не удалось загрузить команды.
          </p>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => {
              setError(false);
              setAttempt((value) => value + 1);
            }}
          >
            Повторить
          </button>
        </>
      ) : hasTeams && !rosters ? (
        <p role="status">Загружаем составы…</p>
      ) : null}
      {!hasTeams ? (
        <p className="muted">Подтверждённых команд пока нет.</p>
      ) : (
        <ul className="confirmed-teams">
          {confirmed.map((team) => {
            const roster = rosters?.find((item) => item.id === team.id && item.name === team.name);
            return (
              <li key={team.id}>
                <Link href={`/teams/${team.id}`}>{team.name}</Link>
                {roster && (
                  <p className="muted">
                    {roster.members.map((member) => member.nickname).join(", ")}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
