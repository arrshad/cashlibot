"""All SQLModel table models are imported here so Alembic sees them on autogenerate."""

from app.models.account import Account, AccountType
from app.models.budget import Budget, BudgetPeriod
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category, CategoryType
from app.models.credit import CreditReason, CreditTransaction
from app.models.frequency import Frequency
from app.models.gamification import (
    STREAK_BUDGET_ADHERENCE,
    STREAK_DAILY_LOG,
    STREAK_SAVINGS_CONTRIBUTION,
    Badge,
    UserBadge,
    UserStreak,
    UserXP,
)
from app.models.memory import EMBEDDING_DIM, MemoryType, UserMemory
from app.models.reminder import Reminder, ReminderType
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.models.user import User

__all__ = [
    "Account",
    "AccountType",
    "Badge",
    "Budget",
    "BudgetPeriod",
    "CategorizationRule",
    "Category",
    "CategoryType",
    "CreditReason",
    "CreditTransaction",
    "EMBEDDING_DIM",
    "Frequency",
    "MemoryType",
    "Reminder",
    "ReminderType",
    "SavingsGoal",
    "STREAK_BUDGET_ADHERENCE",
    "STREAK_DAILY_LOG",
    "STREAK_SAVINGS_CONTRIBUTION",
    "Transaction",
    "TransactionSource",
    "TransactionType",
    "User",
    "UserBadge",
    "UserMemory",
    "UserStreak",
    "UserXP",
]
