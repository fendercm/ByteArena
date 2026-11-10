"use client";

import { useEffect, useRef, useState } from "react";

export default function TournamentLink({ id }) {
  const [url, setUrl] = useState("");
  const [message, setMessage] = useState("");
  const input = useRef(null);
  useEffect(() => {
    setUrl(`${window.location.origin}/tournaments/${id}`);
  }, [id]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setMessage("Ссылка скопирована");
    } catch {
      input.current?.select();
      setMessage("Ссылка выделена. Нажмите Ctrl+C или скопируйте её вручную.");
    }
  }

  return (
    <div className="share-link">
      <label htmlFor="tournament-url">Ссылка на турнир</label>
      <div className="copy-row">
        <input ref={input} id="tournament-url" readOnly value={url} />
        <button className="button secondary" onClick={copy} disabled={!url}>
          Скопировать
        </button>
      </div>
      <span className="muted" role="status">
        {message}
      </span>
    </div>
  );
}
