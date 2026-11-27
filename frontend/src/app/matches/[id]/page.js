"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, formatDate } from "@/lib/api";
import "../../tournaments/tournaments.css";
import "./match.css";

const statuses = { scheduled: "Запланирован", live: "Идёт", finished: "Завершён" };
const roles = { captain: "Капитан", main: "Основной состав", sub: "Запасной" };

function MatchTeam({ team, winner, emptyLabel }) {
  if (!team)
    return (
      <section className="panel match-team">
        <h2>{emptyLabel}</h2>
      </section>
    );
  return (
    <section
      className={`panel match-team${winner ? " match-team-winner" : ""}`}
      aria-label={`Состав: ${team.name}`}
    >
      <h2>
        <Link href={`/teams/${team.id}`}>{team.name}</Link>
      </h2>
      {winner && <p className="match-winner-label">Победитель</p>}
      {team.members.length ? (
        <ul className="match-roster">
          {team.members.map((member, index) => (
            <li key={`${member.user_id ?? member.nickname}-${index}`}>
              {member.user_id != null ? (
                <Link href={`/users/${member.user_id}`}>{member.nickname}</Link>
              ) : (
                <span>{member.nickname}</span>
              )}
              <span className="muted">{roles[member.role] ?? member.role}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">Состав пока не заполнен.</p>
      )}
    </section>
  );
}

export default function MatchPage({ params }) {
  const [match, setMatch] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const matchId = params.id;

  useEffect(() => {
    const controller = new AbortController();
    setMatch(null);
    setError(null);
    api.getMatch(matchId, controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setMatch(data);
      },
      (err) => {
        if (!controller.signal.aborted) setError(err);
      },
    );
    return () => controller.abort();
  }, [matchId, attempt]);

  if (error)
    return (
      <section className="tournament-page page-stack">
        <Link className="back-link" href="/">
          ← Все турниры
        </Link>
        <h1>{error.status === 404 ? "Матч не найден" : "Не удалось загрузить матч"}</h1>
        {error.status !== 404 && (
          <div>
            <button className="button" onClick={() => setAttempt((value) => value + 1)}>
              Повторить
            </button>
          </div>
        )}
      </section>
    );
  if (!match) return <p role="status">Загружаем матч…</p>;

  const winner = [match.team1, match.team2].find((team) => team?.id === match.winner_id);
  const bye = match.status === "finished" && !!winner && (!match.team1 || !match.team2);
  return (
    <section className="tournament-page page-stack match-page">
      <Link className="back-link" href={`/tournaments/${match.tournament_id}`}>
        ← К сетке турнира
      </Link>
      <div className="title-row">
        <div>
          <p className="muted">
            Раунд {match.round} · Пара {match.position}
          </p>
          <h1>Матч #{match.id}</h1>
        </div>
        <span className={`badge badge-${match.status}`}>
          {statuses[match.status] ?? match.status}
        </span>
      </div>
      <div className="panel match-summary">
        <p>
          {match.scheduled_at ? (
            <>
              Начало · МСК:{" "}
              <time dateTime={match.scheduled_at}>{formatDate(match.scheduled_at)}</time>
            </>
          ) : (
            "Время матча уточняется"
          )}
        </p>
        <p className="match-score" aria-label="Счёт матча">
          {match.score1 ?? "—"} : {match.score2 ?? "—"}
        </p>
        <p>
          {bye ? (
            "Проход без игры"
          ) : winner ? (
            <>
              Победитель: <Link href={`/teams/${winner.id}`}>{winner.name}</Link>
            </>
          ) : (
            "Победитель пока не определён"
          )}
        </p>
      </div>
      <div className="match-teams">
        <MatchTeam
          key={`first-${match.team1?.id ?? "empty"}`}
          team={match.team1}
          winner={!!match.team1 && match.team1.id === match.winner_id}
          emptyLabel={bye ? "Проход без игры" : "Соперник ещё не определён"}
        />
        <MatchTeam
          key={`second-${match.team2?.id ?? "empty"}`}
          team={match.team2}
          winner={!!match.team2 && match.team2.id === match.winner_id}
          emptyLabel={bye ? "Проход без игры" : "Соперник ещё не определён"}
        />
      </div>
      {match.next_match_id != null && (
        <Link className="back-link" href={`/matches/${match.next_match_id}`}>
          Следующий матч →
        </Link>
      )}
    </section>
  );
}
