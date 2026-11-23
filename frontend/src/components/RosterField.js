"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function PlayerAvatar({ player }) {
  const [failed, setFailed] = useState(null);
  return (
    <span className="header-avatar" aria-hidden="true">
      {player.avatar_url && player.avatar_url !== failed ? (
        <Image
          src={player.avatar_url}
          alt=""
          width={24}
          height={24}
          unoptimized
          onError={() => setFailed(player.avatar_url)}
        />
      ) : (
        Array.from(player.nickname)[0]?.toUpperCase() || "?"
      )}
    </span>
  );
}

export default function RosterField({ id, label, member, onChange, error, captainId, required }) {
  const query = member.nickname.trim();
  const [search, setSearch] = useState(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (!active || member.player || query.length < 2) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const players = await api.searchUsers(query, controller.signal);
        if (!controller.signal.aborted) {
          setSearch({ query, players: players.filter((player) => player.id !== captainId) });
        }
      } catch {
        if (!controller.signal.aborted) setSearch({ query, unavailable: true });
      }
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [active, captainId, member.player, query]);

  const result =
    active && !member.player && query.length >= 2 && search?.query === query ? search : null;
  return (
    <div
      className="field"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setActive(false);
      }}
    >
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        value={member.nickname}
        onFocus={() => setActive(true)}
        onChange={(event) => {
          setSearch(null);
          setActive(true);
          onChange({ nickname: event.target.value, player: null });
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") setActive(false);
        }}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        autoComplete="off"
        required={required}
      />
      {member.player && (
        <p className="roster-player">
          <PlayerAvatar player={member.player} /> ✓ На сайте
        </p>
      )}
      {result?.players?.length > 0 && (
        <ul className="roster-suggestions" aria-label={`Подсказки: ${label}`}>
          {result.players.map((player) => (
            <li key={player.id}>
              <button
                type="button"
                className="button button-secondary"
                onClick={() => {
                  onChange({ nickname: player.nickname, player });
                  setActive(false);
                  document.getElementById(id)?.focus();
                }}
              >
                <PlayerAvatar player={player} /> {player.nickname}
              </button>
            </li>
          ))}
        </ul>
      )}
      {result?.unavailable && <p className="muted">Поиск недоступен. Можно ввести ник вручную.</p>}
      {error && (
        <p className="field-error" id={`${id}-error`}>
          {error}
        </p>
      )}
    </div>
  );
}
