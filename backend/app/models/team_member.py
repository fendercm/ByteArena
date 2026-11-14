from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TeamMember(Base):
    """Место в составе команды: зарегистрированный игрок (user_id) или просто ник без аккаунта."""

    __tablename__ = "team_members"
    __table_args__ = (
        CheckConstraint("role IN ('captain', 'main', 'sub')", name="role"),
        # зарегистрированный игрок не попадает в одну команду дважды; у ников без аккаунта
        # user_id пустой, а пустые значения уникальность не нарушают
        UniqueConstraint("team_id", "user_id"),
        # частичный уникальный индекс: среди строк с role = 'captain' team_id не повторяется,
        # то есть у команды не больше одного капитана
        Index(
            "uq_team_members_one_captain",
            "team_id",
            unique=True,
            postgresql_where=text("role = 'captain'"),
            sqlite_where=text("role = 'captain'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # заполняется и у зарегистрированных игроков, чтобы страницам не искать ник отдельно
    nickname: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(16))
