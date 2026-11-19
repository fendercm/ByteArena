import pytest

from app.services.bracket import format_bracket, next_slot, plan_bracket

TEAM_COUNTS = [2, 3, 4, 5, 6, 7, 8, 16]


def teams(n: int) -> list[int]:
    return list(range(101, 101 + n))


def places(n: int) -> int:
    return 1 << (n - 1).bit_length()


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_matches_count_is_places_minus_one(n: int) -> None:
    assert len(plan_bracket(teams(n))) == places(n) - 1


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_each_team_plays_once_in_first_round(n: int) -> None:
    first_round = [m for m in plan_bracket(teams(n)) if m.round == 1]
    slots = [t for m in first_round for t in (m.team1_id, m.team2_id) if t is not None]
    assert sorted(slots) == teams(n)


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_byes_count_is_places_minus_teams(n: int) -> None:
    byes = [m for m in plan_bracket(teams(n)) if m.is_bye]
    assert len(byes) == places(n) - n
    # проход без игры: одна команда, она же победитель, матч только в первом раунде
    assert all(m.round == 1 and m.team2_id is None and m.winner_id == m.team1_id for m in byes)


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_single_final(n: int) -> None:
    plan = plan_bracket(teams(n))
    last_round = max(m.round for m in plan)
    assert last_round == places(n).bit_length() - 1
    assert [(m.round, m.position) for m in plan if m.round == last_round] == [(last_round, 1)]


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_every_match_leads_to_existing_next_match(n: int) -> None:
    plan = plan_bracket(teams(n))
    positions = {(m.round, m.position) for m in plan}
    last_round = max(m.round for m in plan)
    for m in plan:
        if m.round < last_round:
            assert next_slot(m.round, m.position)[:2] in positions


@pytest.mark.parametrize("n", TEAM_COUNTS)
def test_bye_winners_already_wait_in_second_round(n: int) -> None:
    plan = {(m.round, m.position): m for m in plan_bracket(teams(n))}
    for (round_, position), m in plan.items():
        if m.is_bye:
            r2, p2, slot = next_slot(round_, position)
            assert getattr(plan[(r2, p2)], slot) == m.winner_id


@pytest.mark.parametrize(
    ("n", "matches", "byes", "rounds"),
    [(4, 3, 0, 2), (5, 7, 3, 3), (6, 7, 2, 3), (8, 7, 0, 3), (16, 15, 0, 4)],
)
def test_table_from_plan(n: int, matches: int, byes: int, rounds: int) -> None:
    plan = plan_bracket(teams(n))
    assert len(plan) == matches
    assert sum(m.is_bye for m in plan) == byes
    assert max(m.round for m in plan) == rounds


def test_next_slot_odd_goes_to_team1_even_to_team2() -> None:
    assert next_slot(1, 1) == (2, 1, "team1_id")
    assert next_slot(1, 2) == (2, 1, "team2_id")
    assert next_slot(1, 3) == (2, 2, "team1_id")
    assert next_slot(2, 2) == (3, 1, "team2_id")


@pytest.mark.parametrize("team_ids", [[], [1]])
def test_needs_at_least_two_teams(team_ids: list[int]) -> None:
    with pytest.raises(ValueError, match="минимум 2 команды"):
        plan_bracket(team_ids)


def test_teams_must_not_repeat() -> None:
    with pytest.raises(ValueError, match="повторяются"):
        plan_bracket([1, 2, 2])


def test_format_bracket_for_five_teams() -> None:
    text = format_bracket(plan_bracket([1, 2, 3, 4, 5]), names={5: "Night Wolves"})
    assert text.splitlines() == [
        "Раунд 1",
        "  1.1  Команда 1 — проход без игры",
        "  1.2  Команда 2 — проход без игры",
        "  1.3  Команда 3 — проход без игры",
        "  1.4  Команда 4  vs  Night Wolves",
        "Раунд 2",
        "  2.1  Команда 1  vs  Команда 2",
        "  2.2  Команда 3  vs  победитель 1.4",
        "Финал",
        "  3.1  победитель 2.1  vs  победитель 2.2",
    ]
