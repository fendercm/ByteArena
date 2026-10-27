from fastapi import FastAPI

from app.routers import health

# root_path="/api": снаружи (через Caddy) API доступен по /api/..., а документация — по /api/docs
app = FastAPI(title="ByteArena API", version="0.1.0", root_path="/api")

app.include_router(health.router)
# Новые роутеры подключаются здесь:
#   from app.routers import tournaments
#   app.include_router(tournaments.router)
