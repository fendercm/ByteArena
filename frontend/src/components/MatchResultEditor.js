"use client";

import { useState } from "react";
import { api } from "@/lib/api";

// В матчах из GET /tournaments/{id} только id команд: названия берём из tournament.teams.
export default function MatchResultEditor({ matches, teams, onUpdated }) {
  const names = new Map(teams.map((team) => [team.id, team.name]));
  const teamName = (id) => (id == null ? "Ожидает соперника" : (names.get(id) ?? `Команда #${id}`));
  const [scores, setScores] = useState({});
  const [busyId, setBusyId] = useState(null);
  const [errors, setErrors] = useState({});
  const ordered = [...matches].sort((a, b) => a.round - b.round || a.position - b.position);
  const rounds = [...new Set(ordered.map((match) => match.round))];

  async function save(match) {
    const score = scores[match.id] ?? {
      score1: match.score1 ?? "",
      score2: match.score2 ?? "",
    };
    const score1 = Number(score.score1);
    const score2 = Number(score.score2);
    if (
      score.score1 === "" ||
      score.score2 === "" ||
      !Number.isInteger(score1) ||
      !Number.isInteger(score2) ||
      score1 < 0 ||
      score2 < 0 ||
      score1 === score2
    ) {
      setErrors((prev) => ({
        ...prev,
        [match.id]: "Введите два целых неотрицательных числа. Ничья невозможна.",
      }));
      return;
    }

    setBusyId(match.id);
    setErrors((prev) => ({ ...prev, [match.id]: "" }));
    try {
      await api.setMatchResult(match.id, { score1, score2 });
      onUpdated(await api.getTournament(match.tournament_id));
      setScores((prev) => ({ ...prev, [match.id]: { score1, score2 } }));
    } catch (error) {
      setErrors((prev) => ({ ...prev, [match.id]: error.message || "Не удалось сохранить счёт" }));
    } finally {
      setBusyId(null);
    }
  }

  if (!ordered.length) return <p className="muted">Матчи ещё не созданы.</p>;

  return (
    <div className="manage-matches">
      {rounds.map((round) => (
        <section className="manage-match-round" key={round}>
          <h3>{round === rounds.at(-1) ? "Финал" : `Раунд ${round}`}</h3>
          {ordered
            .filter((match) => match.round === round)
            .map((match) => {
              const score = scores[match.id] ?? {
                score1: match.score1 ?? "",
                score2: match.score2 ?? "",
              };
              const ready = match.team1_id != null && match.team2_id != null;
              // проход без игры: матч сохранён завершённым, единственная команда уже победила
              const bye = !ready && match.status === "finished" && match.winner_id != null;
              return (
                <article className="manage-match-card" key={match.id}>
                  <div>
                    <strong>
                      Матч {match.round}.{match.position}
                    </strong>
                    <p className="muted">
                      {bye
                        ? `${teamName(match.winner_id)} — проход без игры`
                        : `${teamName(match.team1_id)} — ${teamName(match.team2_id)}`}
                    </p>
                    <p className="muted">
                      {bye
                        ? "Команда сразу проходит в следующий раунд"
                        : match.status === "finished"
                          ? "Завершён"
                          : "Ожидает результата"}
                    </p>
                  </div>
                  {ready ? (
                    <div className="manage-score-controls">
                      <label>
                        <span className="sr-only">Счёт первой команды</span>
                        <input
                          type="number"
                          min="0"
                          step="1"
                          value={score.score1}
                          disabled={busyId === match.id}
                          onChange={(event) =>
                            setScores((prev) => ({
                              ...prev,
                              [match.id]: { ...score, score1: event.target.value },
                            }))
                          }
                        />
                      </label>
                      <span>:</span>
                      <label>
                        <span className="sr-only">Счёт второй команды</span>
                        <input
                          type="number"
                          min="0"
                          step="1"
                          value={score.score2}
                          disabled={busyId === match.id}
                          onChange={(event) =>
                            setScores((prev) => ({
                              ...prev,
                              [match.id]: { ...score, score2: event.target.value },
                            }))
                          }
                        />
                      </label>
                      <button
                        type="button"
                        className="button button-small"
                        disabled={busyId === match.id}
                        onClick={() => save(match)}
                      >
                        {busyId === match.id ? "Сохраняем…" : "Сохранить"}
                      </button>
                    </div>
                  ) : bye ? null : (
                    <p className="muted">Ожидаем победителей предыдущих матчей.</p>
                  )}
                  {errors[match.id] && (
                    <p className="error-message" role="alert">
                      {errors[match.id]}
                    </p>
                  )}
                </article>
              );
            })}
        </section>
      ))}
    </div>
  );
}
