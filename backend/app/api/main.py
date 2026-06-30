"""FastAPI app entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

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


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness + DB connectivity check. Used by Docker and load balancers."""
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}
