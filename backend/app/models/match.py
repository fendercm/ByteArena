from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("tournament_id", "round", "position"),
        CheckConstraint("status IN ('scheduled', 'live', 'finished')", name="status"),
        CheckConstraint("winner_id IS NULL OR winner_id IN (team1_id, team2_id)", name="winner"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"))
    round: Mapped[int]  # 1 = первый раунд
    position: Mapped[int]  # номер матча внутри раунда, с 1
    team1_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team2_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    score1: Mapped[int | None]
    score2: Mapped[int | None]
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    status: Mapped[str] = mapped_column(String(16), server_default="scheduled")
    scheduled_at: Mapped[datetime | None]
    # куда уходит победитель: нечётная position → team1, чётная → team2; у финала NULL
    next_match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id", ondelete="SET NULL"))
