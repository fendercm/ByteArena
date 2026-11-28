"use client";

import Image from "next/image";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api, formatDate } from "@/lib/api";
import "./team.css";

const tournamentStatuses = {
  draft: "Черновик",
  registration: "Регистрация",
  closed: "Регистрация закрыта",
  running: "Идёт",
  finished: "Завершён",
};

const resultLabel = (tournament) => {
  if (tournament.result === "champion") return "Чемпион";

  if (tournament.result === "eliminated") {
    return tournament.eliminated_round
      ? `Выбыли в раунде ${tournament.eliminated_round}`
      : "Выбыли";
  }

  if (tournament.result === "running") return "Идёт";

  return null;
};

const applicationStatuses = {
  pending: "На рассмотрении",
  approved: "Подтверждена",
  rejected: "Отклонена",
};

function Member({ member }) {
  const content = (
    <>
      {member.avatar_url ? (
        <Image
          className="team-member-avatar"
          src={member.avatar_url}
          alt=""
          width={40}
          height={40}
          unoptimized
        />
      ) : (
        <span className="team-member-avatar team-member-placeholder" aria-hidden="true">
          {member.nickname.trim().charAt(0).toUpperCase() || "?"}
        </span>
      )}

      <span className="team-member-name">{member.nickname}</span>
      {member.role === "captain" && <span className="team-role">Капитан</span>}
      {member.user_id === null && <span className="team-offline">не на сайте</span>}
    </>
  );

  return (
    <li className="team-member">
      {member.user_id !== null ? (
        <Link className="team-member-link" href={`/users/${member.user_id}`}>
          {content}
        </Link>
      ) : (
        <div className="team-member-link">{content}</div>
      )}
    </li>
  );
}

export default function TeamPage({ params }) {
  const { id } = use(params);
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError("");
    setTeam(null);

    api
      .getTeam(id, controller.signal)
      .then(setTeam, (err) => {
        if (controller.signal.aborted) return;

        setError(err.status === 404 ? "Команда не найдена" : "Не удалось загрузить команду");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [id, attempt]);

  if (loading) {
    return (
      <section className="team-page page-stack">
        <p role="status">Загружаем профиль команды…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="team-page page-stack">
        <Link className="back-link" href="/">
          ← Все турниры
        </Link>

        <h1>{error}</h1>

        {error !== "Команда не найдена" && (
          <button className="button" onClick={() => setAttempt((value) => value + 1)}>
            Повторить
          </button>
        )}
      </section>
    );
  }

  const mainMembers = team.members.filter(
    (member) => member.role === "main" || member.role === "captain",
  );

  const substitutes = team.members.filter((member) => member.role === "sub");

  return (
    <section className="team-page page-stack">
      <Link className="back-link" href="/">
        ← Все турниры
      </Link>

      <header className="team-heading">
        <div>
          <p className="team-eyebrow">Профиль команды</p>
          <h1>{team.name}</h1>
        </div>

        <div className="team-captain panel">
          <span className="muted">Капитан</span>
          <Link href={`/users/${team.captain.id}`}>{team.captain.nickname}</Link>
        </div>
      </header>

      <div className="team-rosters">
        <section className="panel" aria-labelledby="main-roster-title">
          <div className="section-heading">
            <h2 id="main-roster-title">Основной состав</h2>
            <span className="muted">{mainMembers.length} игроков</span>
          </div>

          {mainMembers.length ? (
            <ul className="team-member-list">
              {mainMembers.map((member, index) => (
                <Member key={`${member.user_id ?? member.nickname}-${index}`} member={member} />
              ))}
            </ul>
          ) : (
            <p className="muted">Основной состав пока не заполнен.</p>
          )}
        </section>

        <section className="panel" aria-labelledby="sub-roster-title">
          <div className="section-heading">
            <h2 id="sub-roster-title">Запасные</h2>
            <span className="muted">{substitutes.length} игроков</span>
          </div>

          {substitutes.length ? (
            <ul className="team-member-list">
              {substitutes.map((member, index) => (
                <Member key={`${member.user_id ?? member.nickname}-${index}`} member={member} />
              ))}
            </ul>
          ) : (
            <p className="muted">Запасных пока нет.</p>
          )}
        </section>
      </div>

      <section className="panel" aria-labelledby="team-tournaments-title">
        <div className="section-heading">
          <h2 id="team-tournaments-title">Турниры команды</h2>
          <span className="muted">{team.tournaments.length}</span>
        </div>

        {team.tournaments.length ? (
          <ul className="team-tournament-list">
            {team.tournaments.map((tournament) => (
              <li key={tournament.id} className="team-tournament">
                <div>
                  <Link href={`/tournaments/${tournament.id}`} className="team-tournament-title">
                    {tournament.title}
                  </Link>

                  <p className="muted">{formatDate(tournament.starts_at)}</p>
                </div>

                <div className="team-tournament-statuses">
                  <span className={`badge badge-${tournament.status}`}>
                    {tournamentStatuses[tournament.status] ?? tournament.status}
                  </span>

                  <span className={`badge badge-${tournament.application_status}`}>
                    Заявка:{" "}
                    {applicationStatuses[tournament.application_status] ??
                      tournament.application_status}
                  </span>

                  {resultLabel(tournament) && (
                    <span className="badge">{resultLabel(tournament)}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Команда ещё не участвовала в турнирах.</p>
        )}
      </section>
    </section>
  );
}
