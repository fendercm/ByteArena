"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, formatDate } from "@/lib/api";
import { discordLoginUrl } from "@/lib/auth";
import "../../tournaments.css";
import MatchResultEditor from "@/components/MatchResultEditor";

const MIN_TEAMS_TO_CLOSE = 2;

const tournamentStatuses = {
  draft: "Черновик",
  registration: "Регистрация",
  closed: "Регистрация закрыта",
  running: "Идёт",
  finished: "Завершён",
};

const GROUPS = [
  { status: "pending", title: "Ждут решения", empty: "Новых заявок нет." },
  { status: "approved", title: "Подтверждены", empty: "Подтверждённых команд пока нет." },
  { status: "rejected", title: "Отклонены", empty: "Отклонённых заявок нет." },
];

const ROLE_LABELS = {
  captain: "капитан",
  sub: "запасной",
};

function MemberAvatar({ member }) {
  const [failed, setFailed] = useState(false);

  return (
    <span className="header-avatar" aria-hidden="true">
      {member.avatar_url && !failed ? (
        <Image
          src={member.avatar_url}
          alt=""
          width={24}
          height={24}
          unoptimized
          onError={() => setFailed(true)}
        />
      ) : (
        Array.from(member.nickname)[0]?.toUpperCase() || "?"
      )}
    </span>
  );
}

function RegistrationCard({ registration, isRegistrationOpen, isFull, isBusy, error, onDecide }) {
  const captain = registration.members.find((member) => member.role === "captain");
  const canApprove = registration.status !== "approved";
  const canReject = registration.status !== "rejected";

  return (
    <article className="registration-card">
      <div className="registration-card-head">
        <div>
          <h3>
            <Link href={`/teams/${registration.team.id}`}>{registration.team.name}</Link>
          </h3>
          <p className="muted registration-meta">
            Капитан: {captain ? captain.nickname : "не указан"}
            {registration.created_at && ` · Подана ${formatDate(registration.created_at)}`}
          </p>
        </div>

        {isRegistrationOpen && (
          <div className="registration-actions">
            {canApprove && (
              <button
                type="button"
                className="button button-small"
                disabled={isFull || isBusy}
                title={isFull ? "Все места заняты" : undefined}
                onClick={() => onDecide(registration.id, "approved")}
              >
                {isBusy ? "Сохраняем…" : "Подтвердить"}
              </button>
            )}
            {canReject && (
              <button
                type="button"
                className="button button-secondary button-small"
                disabled={isBusy}
                onClick={() => onDecide(registration.id, "rejected")}
              >
                {isBusy ? "Сохраняем…" : "Отклонить"}
              </button>
            )}
          </div>
        )}
      </div>

      {isRegistrationOpen && canApprove && isFull && (
        <p className="muted registration-hint">Все места заняты</p>
      )}

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

      <ul className="roster-list">
        {registration.members.map((member, index) => (
          <li key={`${member.nickname}-${index}`} className="roster-member">
            {member.user_id !== null ? (
              <>
                <MemberAvatar member={member} />
                <Link href={`/users/${member.user_id}`} className="roster-link">
                  {member.nickname}
                </Link>
              </>
            ) : (
              <>
                <span>{member.nickname}</span>
                <span className="member-tag">не на сайте</span>
              </>
            )}
            {ROLE_LABELS[member.role] && (
              <span className="muted member-role">({ROLE_LABELS[member.role]})</span>
            )}
          </li>
        ))}
      </ul>
    </article>
  );
}

export default function TournamentManagePage({ params }) {
  const { user, loading: authLoading, error: authError, refresh } = useAuth();
  const [tournament, setTournament] = useState(null);
  const [registrations, setRegistrations] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  const [busyId, setBusyId] = useState(null);
  const [cardErrors, setCardErrors] = useState({});

  const [confirmClose, setConfirmClose] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closeError, setCloseError] = useState("");

  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState("");
  const [confirmStart, setConfirmStart] = useState(false);

  useEffect(() => {
    if (authLoading || !user) return;
    const controller = new AbortController();
    setLoadError(null);
    setTournament(null);
    setRegistrations([]);

    Promise.all([
      api.getTournament(params.id, controller.signal),
      api.getRegistrations(params.id, controller.signal),
    ])
      .then(([tournamentData, registrationsData]) => {
        if (controller.signal.aborted) return;
        setTournament(tournamentData);
        setRegistrations(registrationsData.items ?? []);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setLoadError({
          status: err.status ?? 0,
          message: err.message || "Не удалось загрузить панель организатора",
        });
      });

    return () => controller.abort();
  }, [params.id, user, authLoading, attempt]);

  async function handleDecide(registrationId, nextStatus) {
    setBusyId(registrationId);
    setCardErrors((prev) => ({ ...prev, [registrationId]: "" }));
    setCloseError("");
    try {
      const updated = await api.decideRegistration(registrationId, nextStatus);
      setRegistrations((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      if (nextStatus !== "approved") {
        setConfirmClose(false);
      }
    } catch (err) {
      setCardErrors((prev) => ({
        ...prev,
        [registrationId]: err.message || "Не удалось обновить заявку",
      }));
    } finally {
      setBusyId(null);
    }
  }

  async function handleCloseRegistration() {
    setClosing(true);
    setCloseError("");
    try {
      const updatedTournament = await api.closeRegistration(tournament.id);
      setTournament((prev) => ({ ...prev, ...updatedTournament }));
      setConfirmClose(false);
    } catch (err) {
      setCloseError(err.message || "Не удалось закрыть регистрацию");
    } finally {
      setClosing(false);
    }
  }

  async function handleStartTournament() {
    setStarting(true);
    setStartError("");
    try {
      const updated = await api.startTournament(tournament.id);
      setTournament(updated);
      setConfirmStart(false);
    } catch (error) {
      setStartError(error.message || "Не удалось запустить турнир");
    } finally {
      setStarting(false);
    }
  }

  if (authLoading) return <p role="status">Проверяем вход…</p>;

  if (authError) {
    return (
      <section className="tournament-page page-stack">
        <p className="error-message" role="alert">
          {authError}
        </p>
        <div>
          <button type="button" className="button button-secondary" onClick={refresh}>
            Повторить
          </button>
        </div>
      </section>
    );
  }

  if (!user || loadError?.status === 401) {
    return (
      <section className="tournament-page page-stack">
        <Link className="back-link" href={`/tournaments/${params.id}`}>
          ← К турниру
        </Link>
        <div className="panel compact-panel">
          <h1>Панель организатора</h1>
          <p className="muted">Войдите через Discord, чтобы управлять заявками турнира.</p>
          <a className="button" href={discordLoginUrl}>
            Войти через Discord
          </a>
        </div>
      </section>
    );
  }

  if (loadError?.status === 403) {
    return (
      <section className="tournament-page page-stack">
        <Link className="back-link" href={`/tournaments/${params.id}`}>
          ← К турниру
        </Link>
        <div className="panel compact-panel">
          <h1>Доступ ограничен</h1>
          <p className="muted">Панель управления доступна только организатору турнира.</p>
          <Link className="button button-secondary" href={`/tournaments/${params.id}`}>
            Вернуться к турниру
          </Link>
        </div>
      </section>
    );
  }

  if (loadError?.status === 404) {
    return (
      <section className="tournament-page page-stack">
        <h1>Турнир не найден</h1>
        <Link href="/">← Все турниры</Link>
      </section>
    );
  }

  if (loadError) {
    return (
      <section className="tournament-page page-stack">
        <h1>Не удалось загрузить панель организатора</h1>
        <p className="error-message" role="alert">
          {loadError.message}
        </p>
        <div>
          <button type="button" className="button" onClick={() => setAttempt((value) => value + 1)}>
            Повторить
          </button>
        </div>
      </section>
    );
  }

  if (!tournament) return <p role="status">Загружаем заявки…</p>;

  const approvedCount = registrations.filter((item) => item.status === "approved").length;
  const isRegistrationOpen = tournament.status === "registration";
  const isFull = approvedCount >= tournament.max_teams;
  const canClose = isRegistrationOpen && approvedCount >= MIN_TEAMS_TO_CLOSE;

  return (
    <section className="tournament-page page-stack">
      <Link className="back-link" href={`/tournaments/${tournament.id}`}>
        ← К странице турнира
      </Link>

      <div className="title-row">
        <div>
          <h1>{tournament.title}</h1>
          <p className="muted">Панель организатора</p>
        </div>
        <span className={`badge badge-${tournament.status}`}>
          {tournamentStatuses[tournament.status]}
        </span>
      </div>

      <div className="panel manage-summary">
        <div className="manage-counter">
          <span className="muted">Заявки команд</span>
          <p className="counter-value">
            Подтверждено {approvedCount} из {tournament.max_teams}
          </p>
        </div>

        {isRegistrationOpen && (
          <div className="close-registration-block">
            {!confirmClose ? (
              <>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={!canClose}
                  title={
                    !canClose
                      ? `Нужно минимум ${MIN_TEAMS_TO_CLOSE} подтверждённые команды`
                      : undefined
                  }
                  onClick={() => {
                    setCloseError("");
                    setConfirmClose(true);
                  }}
                >
                  Закрыть регистрацию
                </button>
                {!canClose && (
                  <p className="muted registration-hint">
                    Нужно минимум {MIN_TEAMS_TO_CLOSE} подтверждённые команды
                  </p>
                )}
              </>
            ) : (
              <div className="confirm-box" role="region" aria-label="Подтверждение закрытия">
                <p>Команды больше не смогут подать заявку. Закрыть?</p>
                <div className="confirm-actions">
                  <button
                    type="button"
                    className="button button-small"
                    disabled={closing || !canClose}
                    onClick={handleCloseRegistration}
                  >
                    {closing ? "Закрываем…" : "Закрыть"}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary button-small"
                    disabled={closing}
                    onClick={() => {
                      setConfirmClose(false);
                      setCloseError("");
                    }}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}
            {closeError && (
              <p className="error-message" role="alert">
                {closeError}
              </p>
            )}
          </div>
        )}
      </div>

      <section className="page-stack" aria-labelledby="applications-heading">
        <h2 id="applications-heading">Заявки команд</h2>

        {GROUPS.map((group) => {
          const items = registrations.filter((item) => item.status === group.status);
          return (
            <div key={group.status} className="panel">
              <div className="group-heading">
                <h3>{group.title}</h3>
                <span className="muted">{items.length}</span>
              </div>

              {items.length === 0 ? (
                <p className="muted">{group.empty}</p>
              ) : (
                <div className="registration-list">
                  {items.map((registration) => (
                    <RegistrationCard
                      key={registration.id}
                      registration={registration}
                      isRegistrationOpen={isRegistrationOpen}
                      isFull={isFull}
                      isBusy={busyId === registration.id}
                      error={cardErrors[registration.id]}
                      onDecide={handleDecide}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </section>

      <div className="panel">
        <h2>Матчи</h2>
        {tournament.status === "closed" ? (
          <div className="close-registration-block">
            <p className="muted">Регистрация закрыта. Можно построить сетку и запустить турнир.</p>
            {!confirmStart ? (
              <button
                type="button"
                className="button"
                disabled={starting}
                onClick={() => setConfirmStart(true)}
              >
                Запустить турнир
              </button>
            ) : (
              <div className="confirm-box" role="region" aria-label="Подтверждение запуска">
                <p>Построить сетку из подтверждённых команд и запустить турнир?</p>
                <div className="confirm-actions">
                  <button
                    type="button"
                    className="button button-small"
                    disabled={starting}
                    onClick={handleStartTournament}
                  >
                    {starting ? "Запускаем…" : "Подтвердить запуск"}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary button-small"
                    disabled={starting}
                    onClick={() => setConfirmStart(false)}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}
            {startError && (
              <p className="error-message" role="alert">
                {startError}
              </p>
            )}
          </div>
        ) : tournament.status === "registration" || tournament.status === "draft" ? (
          <p className="muted">Закройте регистрацию, чтобы перейти к запуску турнира.</p>
        ) : (
          <>
            <MatchResultEditor
              matches={tournament.matches ?? []}
              teams={tournament.teams ?? []}
              onUpdated={setTournament}
            />
            {tournament.status === "finished" && (
              <p className="success-notice" role="status">
                Турнир завершён. Все результаты сохранены.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
