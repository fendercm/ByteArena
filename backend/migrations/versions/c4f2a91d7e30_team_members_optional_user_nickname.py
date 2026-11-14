"""team members: optional user, nickname; registration id; tournament status closed

Revision ID: c4f2a91d7e30
Revises: bd69e012d737
Create Date: 2026-11-14 18:00:00.000000

Написана вручную: autogenerate не умеет заполнять новые колонки у существующих строк.
- team_members: свой id, user_id необязательный (место «просто ник»), nickname обязательный.
  У существующих игроков nickname берётся из users.
- tournament_teams: свой id, чтобы обращаться к заявке как PATCH /registrations/{id};
  пара (tournament_id, team_id) остаётся уникальной.
- tournaments: новый статус closed — регистрация закрыта.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f2a91d7e30"
down_revision: str | None = "bd69e012d737"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_STATUSES = "status IN ('draft', 'registration', 'running', 'finished')"
NEW_STATUSES = "status IN ('draft', 'registration', 'closed', 'running', 'finished')"


def upgrade() -> None:
    # --- team_members ---
    op.add_column("team_members", sa.Column("nickname", sa.String(length=32), nullable=True))
    op.execute(
        "UPDATE team_members SET nickname = LEFT(users.nickname, 32) "
        "FROM users WHERE users.id = team_members.user_id"
    )
    op.alter_column("team_members", "nickname", nullable=False)

    op.drop_constraint(op.f("pk_team_members"), "team_members", type_="primary")
    # SERIAL, как у остальных таблиц; существующие строки нумеруются сразу
    op.execute("ALTER TABLE team_members ADD COLUMN id SERIAL")
    op.create_primary_key(op.f("pk_team_members"), "team_members", ["id"])
    op.alter_column("team_members", "user_id", existing_type=sa.Integer(), nullable=True)
    op.create_unique_constraint(
        op.f("uq_team_members_team_id"), "team_members", ["team_id", "user_id"]
    )

    # --- tournament_teams ---
    op.drop_constraint(op.f("pk_tournament_teams"), "tournament_teams", type_="primary")
    op.execute("ALTER TABLE tournament_teams ADD COLUMN id SERIAL")
    op.create_primary_key(op.f("pk_tournament_teams"), "tournament_teams", ["id"])
    op.create_unique_constraint(
        op.f("uq_tournament_teams_tournament_id"),
        "tournament_teams",
        ["tournament_id", "team_id"],
    )

    # --- tournaments ---
    op.drop_constraint(op.f("ck_tournaments_status"), "tournaments", type_="check")
    op.create_check_constraint(op.f("ck_tournaments_status"), "tournaments", NEW_STATUSES)


def downgrade() -> None:
    # --- tournaments: закрытые турниры снова считаются открытыми ---
    op.execute("UPDATE tournaments SET status = 'registration' WHERE status = 'closed'")
    op.drop_constraint(op.f("ck_tournaments_status"), "tournaments", type_="check")
    op.create_check_constraint(op.f("ck_tournaments_status"), "tournaments", OLD_STATUSES)

    # --- tournament_teams ---
    op.drop_constraint(
        op.f("uq_tournament_teams_tournament_id"), "tournament_teams", type_="unique"
    )
    op.drop_constraint(op.f("pk_tournament_teams"), "tournament_teams", type_="primary")
    op.drop_column("tournament_teams", "id")
    op.create_primary_key(
        op.f("pk_tournament_teams"), "tournament_teams", ["tournament_id", "team_id"]
    )

    # --- team_members: места без аккаунта в старой схеме хранить негде, они удаляются ---
    op.execute("DELETE FROM team_members WHERE user_id IS NULL")
    op.drop_constraint(op.f("uq_team_members_team_id"), "team_members", type_="unique")
    op.drop_constraint(op.f("pk_team_members"), "team_members", type_="primary")
    op.drop_column("team_members", "id")
    op.alter_column("team_members", "user_id", existing_type=sa.Integer(), nullable=False)
    op.create_primary_key(op.f("pk_team_members"), "team_members", ["team_id", "user_id"])
    op.drop_column("team_members", "nickname")
