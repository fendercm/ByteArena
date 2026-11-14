from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TournamentTeam(Base):
    """Заявка команды на турнир. У заявки свой id (PATCH /registrations/{id}),
    а пара (tournament_id, team_id) уникальна: одна команда — одна заявка."""

    __tablename__ = "tournament_teams"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="status"),
        UniqueConstraint("tournament_id", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16), server_default="pending")
