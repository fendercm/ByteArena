"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { discordLoginUrl } from "@/lib/auth";

const registrationLabels = {
  pending: "Заявка на рассмотрении",
  approved: "Ваша команда участвует",
  rejected: "Заявка отклонена",
};

function RegistrationAction({ tournament }) {
  if (tournament.status !== "registration") return <p>Регистрация закрыта</p>;
  if (tournament.teams_count >= tournament.max_teams) return <p>Все места заняты</p>;

  return (
    <Link className="button" href={`/tournaments/${tournament.id}/register`}>
      Зарегистрировать команду
    </Link>
  );
}

function PlayerRegistration({ tournament }) {
  const [registration, setRegistration] = useState(undefined);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const tournamentId = tournament.id;

  useEffect(() => {
    const controller = new AbortController();
    api.getMyRegistration(tournamentId, controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setRegistration(data);
      },
      (err) => {
        if (controller.signal.aborted) return;
        if (err.status === 404) setRegistration(null);
        else setError(true);
      },
    );
    return () => controller.abort();
  }, [attempt, tournamentId]);

  if (error) {
    return (
      <>
        <p className="error-message" role="alert">
          Не удалось проверить заявку.
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
    );
  }
  if (registration === undefined) return <p role="status">Проверяем заявку…</p>;
  if (registration)
    return (
      <p className={`badge badge-${registration.status}`}>
        {registrationLabels[registration.status]}
      </p>
    );
  return <RegistrationAction tournament={tournament} />;
}

export default function TournamentRegistration({ tournament }) {
  const { user, loading, error, refresh } = useAuth();
  const isOrganizer = user?.id === tournament.organizer_id;
  const isOpen = tournament.status === "registration";
  const hasSpace = tournament.teams_count < tournament.max_teams;

  return (
    <section className="panel compact-panel" aria-labelledby="tournament-registration">
      <h2 id="tournament-registration">Участие в турнире</h2>
      {loading ? (
        <p role="status">Проверяем вход…</p>
      ) : error ? (
        <>
          <p className="error-message" role="alert">
            {error}
          </p>
          <button type="button" className="button button-secondary" onClick={refresh}>
            Повторить
          </button>
        </>
      ) : isOrganizer ? (
        <Link className="button" href={`/tournaments/${tournament.id}/manage`}>
          Панель организатора
        </Link>
      ) : user ? (
        <PlayerRegistration key={user.id} tournament={tournament} />
      ) : isOpen && hasSpace ? (
        <a className="button" href={discordLoginUrl}>
          Войти, чтобы зарегистрировать команду
        </a>
      ) : (
        <p>{isOpen ? "Все места заняты" : "Регистрация закрыта"}</p>
      )}
    </section>
  );
}
