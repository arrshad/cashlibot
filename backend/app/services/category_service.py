"""Category CRUD and the default-seed list used at onboarding."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryType


@dataclass(frozen=True)
class CategorySeed:
    name_en: str
    name_fa: str
    type: CategoryType
    icon: str


# Default categories every new user gets seeded with. The user can rename,
# customize, or archive any of these afterwards.
DEFAULT_CATEGORIES: tuple[CategorySeed, ...] = (
    # Income
    CategorySeed("Salary", "حقوق", CategoryType.INCOME, "fa-briefcase"),
    CategorySeed("Freelance", "فریلنس", CategoryType.INCOME, "fa-laptop-code"),
    CategorySeed("Investment", "سرمایه‌گذاری", CategoryType.INCOME, "fa-chart-line"),
    CategorySeed("Gift", "هدیه", CategoryType.INCOME, "fa-gift"),
    CategorySeed("Other Income", "درآمد دیگر", CategoryType.INCOME, "fa-circle-plus"),
    # Expense
    CategorySeed("Food", "غذا", CategoryType.EXPENSE, "fa-utensils"),
    CategorySeed("Groceries", "خرید روزانه", CategoryType.EXPENSE, "fa-cart-shopping"),
    CategorySeed("Transport", "حمل و نقل", CategoryType.EXPENSE, "fa-car"),
    CategorySeed("Housing", "مسکن", CategoryType.EXPENSE, "fa-house"),
    CategorySeed("Bills", "قبض‌ها", CategoryType.EXPENSE, "fa-file-invoice-dollar"),
    CategorySeed("Health", "سلامت", CategoryType.EXPENSE, "fa-heart-pulse"),
    CategorySeed("Shopping", "خرید", CategoryType.EXPENSE, "fa-bag-shopping"),
    CategorySeed("Entertainment", "سرگرمی", CategoryType.EXPENSE, "fa-film"),
    CategorySeed("Education", "آموزش", CategoryType.EXPENSE, "fa-graduation-cap"),
    CategorySeed("Travel", "سفر", CategoryType.EXPENSE, "fa-plane"),
    CategorySeed("Subscriptions", "اشتراک‌ها", CategoryType.EXPENSE, "fa-repeat"),
    CategorySeed("Personal Care", "مراقبت شخصی", CategoryType.EXPENSE, "fa-spa"),
    CategorySeed(
        "Gifts & Donations", "هدیه و کمک", CategoryType.EXPENSE, "fa-hand-holding-heart"
    ),
    CategorySeed("Other Expense", "هزینه دیگر", CategoryType.EXPENSE, "fa-circle-minus"),
)


async def seed_default_categories(
    session: AsyncSession, *, user_id: int, language: str
) -> list[Category]:
    """Insert one row per DEFAULT_CATEGORIES, with `name` localized for the user."""
    use_fa = language == "fa"
    rows = [
        Category(
            user_id=user_id,
            name=seed.name_fa if use_fa else seed.name_en,
            name_en=seed.name_en,
            name_fa=seed.name_fa,
            type=seed.type,
            icon=seed.icon,
        )
        for seed in DEFAULT_CATEGORIES
    ]
    session.add_all(rows)
    await session.flush()
    return rows


async def list_categories(
    session: AsyncSession, *, user_id: int, type: CategoryType | None = None
) -> list[Category]:
    stmt = select(Category).where(
        Category.user_id == user_id, Category.is_archived.is_(False)
    )
    if type is not None:
        stmt = stmt.where(Category.type == type)
    result = await session.execute(stmt)
    return list(result.scalars().all())
