from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TeamMember(Base):
    """Игрок в составе команды. Пара (team_id, user_id) — первичный ключ: дважды в одну команду
    не попасть."""

    __tablename__ = "team_members"
    __table_args__ = (
        CheckConstraint("role IN ('captain', 'main', 'sub')", name="role"),
        # частичный уникальный индекс: среди строк с role = 'captain' team_id не повторяется,
        # то есть у команды не больше одного капитана
        Index(
            "uq_team_members_one_captain",
            "team_id",
            unique=True,
            postgresql_where=text("role = 'captain'"),
        ),
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16))
