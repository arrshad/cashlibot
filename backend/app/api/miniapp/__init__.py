"""Mini App API router — gathers all sub-routers under `/api`."""

from fastapi import APIRouter

from app.api.miniapp import (
    accounts,
    budgets,
    categories,
    config,
    dashboard,
    gamification,
    goals,
    me,
    onboarding,
    reminders,
    transactions,
)

router = APIRouter(prefix="/api", tags=["miniapp"])
router.include_router(me.router)
router.include_router(config.router)
router.include_router(onboarding.router)
router.include_router(accounts.router)
router.include_router(categories.router)
router.include_router(transactions.router)
router.include_router(budgets.router)
router.include_router(goals.router)
router.include_router(reminders.router)
router.include_router(gamification.router)
router.include_router(dashboard.router)

__all__ = ["router"]
