"""Admin API router — Bearer-auth'd endpoints under `/api/admin`."""

from fastapi import APIRouter

from app.api.admin import overview, users

router = APIRouter(prefix="/api/admin", tags=["admin"])
router.include_router(overview.router)
router.include_router(users.router)

__all__ = ["router"]
