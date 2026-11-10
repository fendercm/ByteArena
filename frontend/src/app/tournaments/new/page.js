"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { api, fieldErrors } from "@/lib/api";
import TournamentLoginLink from "@/components/TournamentLoginLink";
import "../tournaments.css";

const initial = { title: "", starts_at: "", max_teams: 8, rules: "" };
const storageKey = "bytearena-tournament-draft";

export default function CreateTournamentPage() {
  const router = useRouter();
  const { user, loading, error: authError, refresh } = useAuth();
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [ready, setReady] = useState(false);
  const [requiresLogin, setRequiresLogin] = useState(false);
  const submitting = useRef(false);

  useEffect(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey));
      if (saved && typeof saved === "object") {
        setValues({
          title: typeof saved.title === "string" ? saved.title : "",
          starts_at: typeof saved.starts_at === "string" ? saved.starts_at : "",
          max_teams: [4, 8, 16].includes(saved.max_teams) ? saved.max_teams : 8,
          rules: typeof saved.rules === "string" ? saved.rules : "",
        });
      }
    } catch {
      /* Форма работает и при запрете sessionStorage. */
    }
    if (new URLSearchParams(window.location.search).has("auth_error")) {
      setError("Вход отменён. Войдите через Discord, чтобы продолжить.");
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(values));
    } catch {
      /* Сохранение черновика необязательно. */
    }
  }, [values, ready]);

  useEffect(() => {
    if (user) setRequiresLogin(false);
  }, [user]);

  function update(event) {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: name === "max_teams" ? Number(value) : value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    if (submitting.current) return;
    const nextErrors = {};
    if (!values.title.trim() || values.title.trim().length > 128)
      nextErrors.title = "Введите название от 1 до 128 символов";
    // datetime-local трактуем как МСК независимо от часового пояса компьютера.
    const startsAt = new Date(`${values.starts_at}:00+03:00`);
    if (!Number.isFinite(startsAt.getTime()) || startsAt <= new Date())
      nextErrors.starts_at = "Укажите будущую дату и время начала";
    if (![4, 8, 16].includes(values.max_teams))
      nextErrors.max_teams = "Выберите 4, 8 или 16 команд";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      document.getElementById(Object.keys(nextErrors)[0])?.focus();
      return;
    }
    submitting.current = true;
    setPending(true);
    setError("");
    try {
      const tournament = await api.createTournament({
        title: values.title.trim(),
        starts_at: startsAt.toISOString(),
        max_teams: values.max_teams,
        rules: values.rules.trim() || null,
      });
      try {
        sessionStorage.removeItem(storageKey);
      } catch {
        /* Без хранения. */
      }
      router.push(`/tournaments/${tournament.id}?created=1`);
    } catch (err) {
      if (err.status === 401) {
        setRequiresLogin(true);
        setError("Сессия истекла. Войдите ещё раз — черновик сохранён в этой вкладке.");
        refresh();
      } else if (err.status === 422) {
        const fields = fieldErrors(err);
        setErrors(fields);
        setError(Object.keys(fields).length ? "Проверьте заполненные поля." : err.message);
        document.getElementById(Object.keys(fields)[0])?.focus();
      } else {
        setError(err.status ? err.message : "Не удалось связаться с сервером. Попробуйте ещё раз.");
      }
      setPending(false);
      submitting.current = false;
    }
  }

  function fieldProps(name) {
    return {
      id: name,
      name,
      value: values[name],
      onChange: update,
      "aria-invalid": Boolean(errors[name]),
      "aria-describedby": errors[name] ? `${name}-error` : undefined,
    };
  }

  return (
    <section className="tournament-page page-stack">
      <div>
        <Link className="back-link" href="/">
          ← Турниры
        </Link>
        <h1>Создать турнир</h1>
      </div>
      {loading || !ready ? (
        <p role="status" className="muted">
          Проверяем вход…
        </p>
      ) : authError ? (
        <div className="panel compact-panel" role="alert">
          <p>{authError}</p>
          <button className="button" onClick={refresh}>
            Повторить
          </button>
        </div>
      ) : !user || requiresLogin ? (
        <div className="panel compact-panel">
          <h2>Сначала войдите</h2>
          <p className="muted">Создавать турниры могут пользователи, вошедшие через Discord.</p>
          {error && (
            <p role="alert" className="error-message">
              {error}
            </p>
          )}
          <TournamentLoginLink />
        </div>
      ) : (
        <form className="panel tournament-form" onSubmit={submit} noValidate aria-busy={pending}>
          <fieldset disabled={pending}>
            <legend className="sr-only">Параметры турнира</legend>
            <div className="field">
              <label htmlFor="title">
                Название турнира <span className="muted">*</span>
              </label>
              <input
                {...fieldProps("title")}
                maxLength={128}
                required
                placeholder="Ночной кубок Arena"
                autoComplete="off"
              />
              {errors.title && (
                <p className="field-error" id="title-error">
                  {errors.title}
                </p>
              )}
            </div>
            <div className="form-row">
              <div className="field">
                <label htmlFor="starts_at">
                  Дата и время начала · МСК <span className="muted">*</span>
                </label>
                <input {...fieldProps("starts_at")} type="datetime-local" required />
                {errors.starts_at && (
                  <p className="field-error" id="starts_at-error">
                    {errors.starts_at}
                  </p>
                )}
              </div>
              <div className="field">
                <label htmlFor="max_teams">
                  Количество команд <span className="muted">*</span>
                </label>
                <select {...fieldProps("max_teams")} required>
                  {[4, 8, 16].map((count) => (
                    <option key={count} value={count}>
                      {count} команд{count === 4 ? "ы" : ""}
                    </option>
                  ))}
                </select>
                {errors.max_teams && (
                  <p className="field-error" id="max_teams-error">
                    {errors.max_teams}
                  </p>
                )}
              </div>
            </div>
            <div className="field">
              <label htmlFor="rules">
                Правила <span className="muted">· необязательно</span>
              </label>
              <textarea
                {...fieldProps("rules")}
                rows={5}
                placeholder="Формат матчей, время ожидания и другие условия"
              />
              {errors.rules && (
                <p className="field-error" id="rules-error">
                  {errors.rules}
                </p>
              )}
            </div>
          </fieldset>
          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <span className="muted">CS2 · время указано по Москве (UTC+3)</span>
            <button className="button" type="submit" disabled={pending}>
              {pending ? "Создаём…" : "Создать турнир"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
