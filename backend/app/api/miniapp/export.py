"""GET /api/export/data.json + /api/export/transactions.csv — GDPR-style data dump."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.services.export_service import (
    _json_default,
    build_json_dump,
    build_transactions_csv,
)

router = APIRouter(prefix="/export")


def _stamped_filename(user: User, stem: str, ext: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"cashlibot-{stem}-{user.telegram_id}-{stamp}.{ext}"


@router.get("/data.json")
async def export_data_json(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    dump = await build_json_dump(session, user=user)
    body = json.dumps(dump, default=_json_default, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_stamped_filename(user, "data", "json")}"'
            )
        },
    )


@router.get("/transactions.csv")
async def export_transactions_csv(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    body = await build_transactions_csv(session, user=user)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_stamped_filename(user, "transactions", "csv")}"'
            )
        },
    )
