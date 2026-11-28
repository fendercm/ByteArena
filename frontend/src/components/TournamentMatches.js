import Link from "next/link";
import { emptySlotLabel } from "@/lib/bracket";
import "./tournament-matches.css";

const statuses = { scheduled: "Запланирован", live: "Идёт", finished: "Завершён" };

export default function TournamentMatches({ tournament }) {
  const matches = [...tournament.matches].sort(
    (a, b) => a.round - b.round || a.position - b.position,
  );
  if (!matches.length) return <p className="muted">Сетка появится после запуска турнира.</p>;
  const rounds = [...new Set(matches.map((match) => match.round))];
  const names = new Map(tournament.teams.map((team) => [team.id, team.name]));
  const teamName = (id) => names.get(id) ?? `Команда #${id}`;
  return (
    <div className="bracket-scroll" role="region" aria-label="Турнирная сетка" tabIndex={0}>
      <div className="tournament-rounds" style={{ "--round-count": rounds.length }}>
        {rounds.map((round) => (
          <section key={round} className="tournament-round" aria-label={`Раунд ${round}`}>
            <h3>{round === rounds.at(-1) ? "Финал" : `Раунд ${round}`}</h3>
            <ul
              style={{ "--match-count": matches.filter((match) => match.round === round).length }}
            >
              {matches
                .filter((match) => match.round === round)
                .map((match) => (
                  <li key={match.id}>
                    <Link className="bracket-match" href={`/matches/${match.id}`}>
                      <span className="muted">
                        Матч {match.round}.{match.position} ·{" "}
                        {statuses[match.status] ?? match.status}
                      </span>
                      {[match.team1_id, match.team2_id].map((id, index) => (
                        <span
                          key={index}
                          className={`bracket-team${id != null && id === match.winner_id ? " bracket-winner" : ""}`}
                        >
                          <span>
                            {id == null ? emptySlotLabel(match, index, matches) : teamName(id)}
                            {id != null && id === match.winner_id && (
                              <span className="bracket-winner-mark" aria-label="Победитель">
                                {" "}
                                ✓
                              </span>
                            )}
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
    </div>
  );
}
