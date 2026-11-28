"use client";

import Link from "next/link";
import { use, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import RosterField, { PlayerAvatar } from "@/components/RosterField";
import { api } from "@/lib/api";
import { discordLoginUrl } from "@/lib/auth";
import "../../tournaments.css";
import "./registration.css";

const slots = Array.from({ length: 6 }, (_, index) => ({
  id: `member-${index + 1}`,
  role: index < 4 ? "main" : "sub",
  label: index < 4 ? `Основной игрок ${index + 1}` : `Запасной ${index - 3}`,
}));

function validate(name, members, captain) {
  const errors = {};
  const names = new Set([captain.nickname.trim().toLowerCase()]);
  const players = new Set([captain.id]);
  if (Array.from(name).length < 2 || Array.from(name).length > 32) {
    errors.name = "Введите название от 2 до 32 символов";
  }
  slots.forEach(({ id, role }, index) => {
    const { nickname, player } = members[index];
    const trimmed = nickname.trim();
    if (!trimmed && role === "sub") return;
    const key = trimmed.toLowerCase();
    if (Array.from(trimmed).length < 2 || Array.from(trimmed).length > 32) {
      errors[id] = "Введите ник от 2 до 32 символов";
    } else if (key === captain.nickname.trim().toLowerCase() || player?.id === captain.id) {
      errors[id] = "Капитан уже включён в состав";
    } else if (names.has(key) || (player && players.has(player.id))) {
      errors[id] = "Игрок уже указан в составе";
    }
    names.add(key);
    if (player) players.add(player.id);
  });
  return errors;
}

export default function TournamentRegisterPage({ params }) {
  const { id } = use(params);
  const { user, loading, error: authError, refresh } = useAuth();
  const [name, setName] = useState("");
  const [members, setMembers] = useState(() => slots.map(() => ({ nickname: "", player: null })));
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const inFlight = useRef(false);
  const createdTeam = useRef(null);
  const tournamentId = id;
  const back = `/tournaments/${encodeURIComponent(tournamentId)}`;

  async function submit(event) {
    event.preventDefault();
    if (inFlight.current || !user) return;
    setError("");
    const cleanName = name.trim();
    const nextErrors = validate(cleanName, members, user);
    setErrors(nextErrors);
    const first = Object.keys(nextErrors)[0];
    if (first) {
      document.getElementById(first)?.focus();
      return;
    }

    const data = {
      name: cleanName,
      members: members.flatMap(({ nickname, player }, index) =>
        nickname.trim()
          ? [{ nickname: nickname.trim(), user_id: player?.id ?? null, role: slots[index].role }]
          : [],
      ),
    };
    const key = JSON.stringify([user.id, tournamentId, data]);
    inFlight.current = true;
    setPending(true);
    try {
      // При ошибке второго запроса повторяем заявку с уже созданной командой.
      if (createdTeam.current?.key !== key) {
        // Команда создаётся до заявки, поэтому сначала проверяем, что заявку ещё примут:
        // иначе после отказа в базе осталась бы лишняя команда.
        const tournament = await api.getTournament(tournamentId);
        if (tournament.status !== "registration") {
          setError("Регистрация закрыта");
          return;
        }
        if (tournament.teams_count >= tournament.max_teams) {
          setError("Мест нет");
          return;
        }
        const team = await api.createTeam(data);
        createdTeam.current = { key, id: team.id };
      }
      await api.registerTeam(tournamentId, createdTeam.current.id);
      setSubmitted(true);
    } catch (failure) {
      setError(failure.status ? failure.message : "Не удалось отправить заявку. Попробуйте снова.");
      if (failure.status === 401) refresh();
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }

  function renderMember(slot, index) {
    return (
      <RosterField
        key={slot.id}
        id={slot.id}
        label={slot.label}
        member={members[index]}
        captainId={user.id}
        required={slot.role === "main"}
        error={errors[slot.id]}
        onChange={(member) => {
          setMembers((current) => current.map((item, i) => (i === index ? member : item)));
          setErrors({});
        }}
      />
    );
  }

  return (
    <section className="tournament-page page-stack team-registration">
      <div>
        <Link className="back-link" href={back}>
          ← К турниру
        </Link>
        <h1>Регистрация команды</h1>
      </div>
      {submitted ? (
        <div className="panel compact-panel">
          <h2>Заявка отправлена</h2>
          <p>Организатор рассмотрит её до начала турнира.</p>
          <Link className="button" href={back}>
            Вернуться на турнир
          </Link>
        </div>
      ) : loading ? (
        <p role="status">Проверяем вход…</p>
      ) : authError ? (
        <div className="panel compact-panel" role="alert">
          <p>{authError}</p>
          <button type="button" className="button" onClick={refresh}>
            Повторить
          </button>
        </div>
      ) : !user ? (
        <div className="panel compact-panel">
          <p>Войдите через Discord, чтобы зарегистрировать команду.</p>
          <a className="button" href={discordLoginUrl}>
            Войти через Discord
          </a>
        </div>
      ) : (
        <form className="panel tournament-form" onSubmit={submit} noValidate aria-busy={pending}>
          <fieldset disabled={pending}>
            <legend className="sr-only">Данные команды</legend>
            <div className="field">
              <label htmlFor="name">Название команды</label>
              <input
                id="name"
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  setErrors((current) => ({ ...current, name: undefined }));
                }}
                required
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? "name-error" : undefined}
              />
              {errors.name && (
                <p className="field-error" id="name-error">
                  {errors.name}
                </p>
              )}
            </div>
            <p className="roster-player">
              <PlayerAvatar player={user} /> <strong>{user.nickname}</strong> · Капитан
            </p>
            <div className="field">
              <h2>Основной состав</h2>
              <p className="muted">Выберите игрока из подсказок или введите ник вручную.</p>
              <div className="form-row">{slots.slice(0, 4).map(renderMember)}</div>
            </div>
            <div className="field">
              <h2>
                Запасные <span className="muted">(необязательно)</span>
              </h2>
              <div className="form-row">
                {slots.slice(4).map((slot, index) => renderMember(slot, index + 4))}
              </div>
            </div>
          </fieldset>
          <div className="form-actions">
            {error && (
              <p className="error-message" role="alert">
                {error}
              </p>
            )}
            <button className="button" type="submit" disabled={pending}>
              {pending ? "Отправляем…" : "Подать заявку"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
