"""Сетка single elimination.

Число мест в сетке — ближайшая степень двойки: 5 команд -> 8 мест -> 3 раунда.
Лишние места — проходы без игры (bye): команда сразу попадает во второй раунд.
Победитель матча с нечётной позицией становится team1 следующего матча, с чётной — team2.

Распечатать сетку: python -m app.services.bracket 5
"""

import random
import sys
from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam


@dataclass
class PlannedMatch:
    round: int
    position: int
    team1_id: int | None = None
    team2_id: int | None = None
    winner_id: int | None = None
    is_bye: bool = False


def next_slot(round_: int, position: int) -> tuple[int, int, str]:
    """Куда уходит победитель: (раунд, позиция, слот)."""
    return round_ + 1, (position + 1) // 2, "team1_id" if position % 2 == 1 else "team2_id"


def plan_bracket(team_ids: list[int]) -> list[PlannedMatch]:
    """Все матчи сетки по раундам. Порядок team_ids задаёт пары, поэтому перед вызовом
    команды стоит перемешать. Bye достаются первым командам списка."""
    n = len(team_ids)
    if n < 2:
        raise ValueError("Для сетки нужно минимум 2 команды")
    if len(set(team_ids)) != n:
        raise ValueError("Команды в сетке повторяются")

    size = 1 << (n - 1).bit_length()  # ближайшая степень двойки: 5 команд -> 8 мест
    rounds = size.bit_length() - 1  # 8 мест -> 3 раунда
    byes = size - n  # сколько команд проходят первый раунд без игры

    matches = {
        (r, p): PlannedMatch(round=r, position=p)
        for r in range(1, rounds + 1)
        for p in range(1, size // 2**r + 1)
    }

    teams = iter(team_ids)
    for p in range(1, size // 2 + 1):
        match = matches[(1, p)]
        match.team1_id = next(teams)
        if p <= byes:
            match.is_bye = True
            match.winner_id = match.team1_id
        else:
            match.team2_id = next(teams)

    for p in range(1, byes + 1):  # победители bye сразу во втором раунде
        r2, p2, slot = next_slot(1, p)
        setattr(matches[(r2, p2)], slot, matches[(1, p)].winner_id)

    return sorted(matches.values(), key=lambda m: (m.round, m.position))


def format_bracket(plan: list[PlannedMatch], names: dict[int, str] | None = None) -> str:
    """Сетка текстом, по раундам. Пустой слот подписан, из какого матча придёт победитель."""
    names = names or {}
    rounds = max(m.round for m in plan)
    lines: list[str] = []

    def slot(team_id: int | None, round_: int, source_position: int) -> str:
        if team_id is not None:
            return names.get(team_id, f"Команда {team_id}")
        return f"победитель {round_ - 1}.{source_position}"

    for round_ in range(1, rounds + 1):
        title = "Финал" if round_ == rounds else f"Раунд {round_}"
        lines.append(title)
        for m in (m for m in plan if m.round == round_):
            left = slot(m.team1_id, m.round, 2 * m.position - 1)
            if m.is_bye:
                lines.append(f"  {m.round}.{m.position}  {left} — проход без игры")
            else:
                right = slot(m.team2_id, m.round, 2 * m.position)
                lines.append(f"  {m.round}.{m.position}  {left}  vs  {right}")
    return "\n".join(lines)


class BracketError(ValueError):
    """Сетку построить нельзя; текст ошибки можно показывать пользователю."""


def save_bracket(
    db: Session, tournament: Tournament, rng: random.Random | None = None
) -> list[Match]:
    """Построить сетку из подтверждённых команд и сохранить все её матчи.

    Порядок команд перемешивается, чтобы пары не зависели от порядка заявок (rng можно
    передать в тестах). Матч с проходом без игры сохраняется завершённым, с победителем.
    Коммит и смену статуса турнира делает вызывающий код — эндпоинт запуска на неделе 4.
    """
    if tournament.status != "closed":
        raise BracketError("Сетку можно построить только после закрытия регистрации")
    if db.scalar(select(exists().where(Match.tournament_id == tournament.id))):
        raise BracketError("Сетка уже построена")

    team_ids = list(
        db.scalars(
            select(TournamentTeam.team_id)
            .where(
                TournamentTeam.tournament_id == tournament.id,
                TournamentTeam.status == "approved",
            )
            .order_by(TournamentTeam.id)
        )
    )
    if len(team_ids) < 2:
        raise BracketError("Для сетки нужно минимум 2 подтверждённые команды")
    (rng or random).shuffle(team_ids)

    rows: dict[tuple[int, int], Match] = {}
    for planned in plan_bracket(team_ids):
        match = Match(
            tournament_id=tournament.id,
            round=planned.round,
            position=planned.position,
            team1_id=planned.team1_id,
            team2_id=planned.team2_id,
            winner_id=planned.winner_id,
            status="finished" if planned.is_bye else "scheduled",
        )
        db.add(match)
        rows[(planned.round, planned.position)] = match
    db.flush()  # у матчей появились id

    for (round_, position), match in rows.items():
        following = rows.get(next_slot(round_, position)[:2])  # у финала следующего матча нет
        match.next_match_id = following.id if following else None
    db.flush()
    return sorted(rows.values(), key=lambda m: (m.round, m.position))


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"Сетка на {count} команд\n")
    print(format_bracket(plan_bracket(list(range(1, count + 1)))))
