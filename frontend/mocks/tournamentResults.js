import matches from "./data/matches.json";

export const registrationRows = [
  { id: 1, tournament_id: 1, team_id: 1, status: "approved" },
  { id: 2, tournament_id: 1, team_id: 2, status: "pending" },
  { id: 3, tournament_id: 2, team_id: 1, status: "rejected" },
  { id: 4, tournament_id: 3, team_id: 1, status: "approved" },
  { id: 5, tournament_id: 7, team_id: 2, status: "approved" },
  { id: 6, tournament_id: 24, team_id: 1, status: "approved" },
  { id: 7, tournament_id: 25, team_id: 1, status: "approved" },
  { id: 8, tournament_id: 26, team_id: 2, status: "approved" },
  { id: 9, tournament_id: 27, team_id: 2, status: "pending" },
  { id: 10, tournament_id: 28, team_id: 1, status: "approved" },
  { id: 11, tournament_id: 29, team_id: 2, status: "approved" },
  { id: 12, tournament_id: 4, team_id: 1, status: "approved" },
];

export function getTournamentResult(tournament, teamId) {
  const teamMatches = matches.filter(
    (match) => match.tournament_id === tournament.id &&
      (match.team1_id === teamId || match.team2_id === teamId),
  );
  const loss = teamMatches.find(
    (match) => match.status === "finished" && match.winner_id !== null && match.winner_id !== teamId,
  );
  if (loss) return { result: "eliminated", eliminated_round: loss.round };
  if (tournament.status === "finished") {
    const final = matches
      .filter((match) => match.tournament_id === tournament.id)
      .sort((a, b) => b.round - a.round)[0];
    if (final?.status === "finished" && final.winner_id === teamId) {
      return { result: "champion", eliminated_round: null };
    }
  }
  if (tournament.status === "running" && teamMatches.length) {
    return { result: "running", eliminated_round: null };
  }
  return { result: null, eliminated_round: null };
}
