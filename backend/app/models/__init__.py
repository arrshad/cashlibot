"""All SQLModel table models are imported here so Alembic sees them on autogenerate."""

from app.models.account import Account, AccountType
from app.models.budget import Budget, BudgetPeriod
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category, CategoryType
from app.models.credit import CreditReason, CreditTransaction
from app.models.memory import EMBEDDING_DIM, MemoryType, UserMemory
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.models.user import User

__all__ = [
    "Account",
    "AccountType",
    "Budget",
    "BudgetPeriod",
    "CategorizationRule",
    "Category",
    "CategoryType",
    "CreditReason",
    "CreditTransaction",
    "EMBEDDING_DIM",
    "MemoryType",
    "SavingsGoal",
    "Transaction",
    "TransactionSource",
    "TransactionType",
    "User",
    "UserMemory",
]
