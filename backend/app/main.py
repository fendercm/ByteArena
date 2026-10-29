from fastapi import FastAPI

from app.routers import health

# root_path="/api": снаружи (через Caddy) API доступен по /api/..., а документация — по /api/docs
app = FastAPI(title="ByteArena API", version="0.1.0", root_path="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
