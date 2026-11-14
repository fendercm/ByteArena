"""Тестовые данные: cd backend && python -m app.seed.

В Docker: docker compose exec backend python -m app.seed.
Миграции должны быть применены заранее. Скрипт только добавляет демоданные.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Team, TeamMember, Tournament, TournamentTeam, User


def seed_data(db: Session) -> dict[str, int]:
    """Вызывать внутри транзакции. Существующие записи сохраняются без изменений."""
    # Не допускаем дубликаты команд и турниров при одновременном запуске в PostgreSQL.
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(728431029)"))

    counts = dict(users=0, teams=0, members=0, tournaments=0, registrations=0)
    players = []
    for number in range(41):
        discord_id = f"bytearena-demo-{number:02}"
        user = db.scalar(select(User).where(User.discord_id == discord_id))
        if user is None:
            user = User(discord_id=discord_id, nickname=f"DemoPlayer{number:02}")
            db.add(user)
            db.flush()
            counts["users"] += 1
        players.append(user)

    teams = []
    for number in range(8):
        roster = players[number * 5 + 1 : number * 5 + 6]
        name = f"ByteArena Demo Team {number + 1}"
        team = db.scalar(select(Team).where(Team.name == name, Team.captain_id == roster[0].id))
        if team is None:
            team = Team(name=name, captain_id=roster[0].id)
            db.add(team)
            db.flush()
            counts["teams"] += 1
        for position, player in enumerate(roster):
            member = db.scalar(
                select(TeamMember).where(
                    TeamMember.team_id == team.id, TeamMember.user_id == player.id
                )
            )
            if member is None:
                db.add(
                    TeamMember(
                        team_id=team.id,
                        user_id=player.id,
                        nickname=player.nickname,
                        role="captain" if position == 0 else "main",
                    )
                )
                counts["members"] += 1
        teams.append(team)

    now = datetime.now(UTC).replace(second=0, microsecond=0)
    examples = [
        ("Arena Cup", "running", 0, 8),
        ("Friday Night Clash", "running", 0, 8),
        ("Weekend Cup", "registration", 3, 6),
        ("Rookie Rush", "registration", 5, 4),
        ("November Open", "registration", 7, 8),
        ("Autumn Cup", "finished", -7, 8),
    ]
    for title, status, days, approved in examples:
        name = f"[DEMO] {title}"
        tournament = db.scalar(
            select(Tournament).where(
                Tournament.title == name, Tournament.organizer_id == players[0].id
            )
        )
        if tournament is None:
            tournament = Tournament(
                title=name,
                description="Демонстрационный турнир для проверки интерфейса ByteArena.",
                game="cs2",
                starts_at=now + timedelta(days=days),
                max_teams=8,
                rules="5×5. Single elimination. BO1.",
                status=status,
                organizer_id=players[0].id,
            )
            db.add(tournament)
            db.flush()
            counts["tournaments"] += 1
        for team in teams[:approved]:
            registration = db.scalar(
                select(TournamentTeam).where(
                    TournamentTeam.tournament_id == tournament.id,
                    TournamentTeam.team_id == team.id,
                )
            )
            if registration is None:
                db.add(
                    TournamentTeam(tournament_id=tournament.id, team_id=team.id, status="approved")
                )
                counts["registrations"] += 1
        # При autoflush=False следующие запросы должны видеть добавленные связи.
        db.flush()
    return counts


if __name__ == "__main__":
    with SessionLocal.begin() as session:
        created = seed_data(session)
    print("Добавлено: " + ", ".join(f"{name}={count}" for name, count in created.items()))
