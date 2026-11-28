export function emptySlotLabel(match, slotIndex, matches) {
  if (match.status === "finished" && match.winner_id != null) {
    return "Проход без игры";
  }

  const source = matches.find(
    (item) => item.next_match_id === match.id && item.position % 2 === (slotIndex === 0 ? 1 : 0),
  );
  if (source) return `Победитель матча ${source.round}.${source.position}`;
  if (match.round > 1) {
    return `Победитель матча ${match.round - 1}.${2 * match.position - 1 + slotIndex}`;
  }
  return "Участник не определён";
}

export function getChampion(tournament) {
  if (tournament.status !== "finished" || !tournament.matches.length) return null;
  const finalRound = Math.max(...tournament.matches.map((match) => match.round));
  const final = tournament.matches.find(
    (match) =>
      match.round === finalRound &&
      match.next_match_id == null &&
      match.status === "finished" &&
      match.winner_id != null,
  );
  if (!final) return null;
  return (
    tournament.teams.find((team) => team.id === final.winner_id) ?? {
      id: final.winner_id,
      name: `Команда #${final.winner_id}`,
    }
  );
}
