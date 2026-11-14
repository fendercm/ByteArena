from fastapi import FastAPI

from app.routers import auth, health, matches, registrations, teams, tournaments, users

# root_path="/api": снаружи (через Caddy) API доступен по /api/..., а документация — по /api/docs
app = FastAPI(title="ByteArena API", version="0.1.0", root_path="/api")

app.include_router(health.router)
app.include_router(tournaments.router)
app.include_router(matches.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(teams.tournaments_router)
app.include_router(registrations.router)
# Новые роутеры подключаются здесь:
#   from app.routers import teams
#   app.include_router(teams.router)
