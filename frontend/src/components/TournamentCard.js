import Link from "next/link";

const statuses = { registration: "Регистрация", running: "Идёт", finished: "Завершён" };

export default function TournamentCard({ tournament }) {
  const { id, title, starts_at, status, teams_count, max_teams } = tournament;
  const date = new Date(starts_at);
  const day = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Europe/Moscow",
  })
    .format(date)
    .replace(/ г\.$/, "");
  const time = new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Moscow",
  }).format(date);
  return (
    <Link href={`/tournaments/${id}`} className="tournament-card">
      <div className="card-top">
        <span className={`badge badge-${status}`}>{statuses[status]}</span>
        <span>CS2 · 5×5</span>
      </div>
      <h3>{title}</h3>
      <p className="card-date">
        <time dateTime={starts_at}>
          {day}, {time} · МСК
        </time>
      </p>
      <div className="card-bottom">
        <span>Single elimination · BO1</span>
        <strong>
          {teams_count}/{max_teams} команд
        </strong>
      </div>
    </Link>
  );
}
