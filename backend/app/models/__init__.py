# Сюда импортируются все модели, чтобы Alembic видел их при autogenerate.
from app.db import Base
from app.models.match import Match
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User

__all__ = ["Base", "Match", "Team", "TeamMember", "Tournament", "TournamentTeam", "User"]
