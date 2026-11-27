import Link from "next/link";
import "./tournament-matches.css";

const statuses = { scheduled: "Запланирован", live: "Идёт", finished: "Завершён" };

export default function TournamentMatches({ tournament }) {
  const matches = [...tournament.matches].sort(
    (a, b) => a.round - b.round || a.position - b.position,
  );
  if (!matches.length) return <p className="muted">Сетка появится после запуска турнира.</p>;
  const rounds = [...new Set(matches.map((match) => match.round))];
  const names = new Map(tournament.teams.map((team) => [team.id, team.name]));
  const teamName = (id) =>
    id == null ? "Соперник не определён" : (names.get(id) ?? `Команда #${id}`);
  return (
    <div className="tournament-rounds">
      {rounds.map((round) => (
        <section key={round} className="tournament-round" aria-label={`Раунд ${round}`}>
          <h3>{round === rounds.at(-1) ? "Финал" : `Раунд ${round}`}</h3>
          <ul>
            {matches
              .filter((match) => match.round === round)
              .map((match) => (
                <li key={match.id}>
                  <Link className="bracket-match" href={`/matches/${match.id}`}>
                    <span className="muted">
                      Матч #{match.id} · {statuses[match.status] ?? match.status}
                    </span>
                    {[match.team1_id, match.team2_id].map((id, index) => (
                      <span
                        key={index}
                        className={`bracket-team${id != null && id === match.winner_id ? " bracket-winner" : ""}`}
                      >
                        <span>
                          {id == null && match.status === "finished" && match.winner_id != null
                            ? "Проход без игры"
                            : teamName(id)}
                        </span>
                        <span>{(index === 0 ? match.score1 : match.score2) ?? "—"}</span>
                      </span>
                    ))}
                  </Link>
                </li>
              ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
