"""Mini App API router — gathers all sub-routers under `/api`."""

from fastapi import APIRouter

from app.api.miniapp import config, me, onboarding

router = APIRouter(prefix="/api", tags=["miniapp"])
router.include_router(me.router)
router.include_router(config.router)
router.include_router(onboarding.router)

__all__ = ["router"]
