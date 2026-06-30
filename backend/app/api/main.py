"""FastAPI app entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.miniapp import router as miniapp_router
from app.core.bootstrap import load_app_context
from app.core.config import get_settings
from app.core.db import async_session_factory, engine
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    load_app_context()
    yield
    await engine.dispose()


app = FastAPI(title="Cashlibot API", version="0.1.0", lifespan=lifespan)


# The Mini App lives at a different origin in dev (Vite at :5173) and in prod
# (whatever MINIAPP_URL points at). We allow both — Telegram WebApp passes
# initData in the Authorization header, so credentials aren't relied upon here.
_settings = get_settings()
_allowed_origins: list[str] = ["http://localhost:5173"]
if _settings.miniapp_url:
    _allowed_origins.append(_settings.miniapp_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(miniapp_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness + DB connectivity check. Used by Docker and load balancers."""
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}
