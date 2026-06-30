"""GET /api/config — choices the Mini App needs to render onboarding & settings."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.bootstrap import load_app_context
from app.models.account import AccountType

router = APIRouter()


# Same curated list the bot's docs reference; users can type anything in the
# free-text fallback that the Mini App offers if they don't see their zone here.
POPULAR_TIMEZONES: tuple[tuple[str, str], ...] = (
    ("Asia/Tehran", "Tehran"),
    ("Asia/Dubai", "Dubai"),
    ("Europe/Istanbul", "Istanbul"),
    ("Europe/London", "London"),
    ("Europe/Paris", "Paris"),
    ("America/New_York", "New York"),
    ("America/Los_Angeles", "Los Angeles"),
    ("Asia/Tokyo", "Tokyo"),
    ("UTC", "UTC"),
)


class CurrencyOption(BaseModel):
    code: str
    name: str
    symbol: str
    symbol_position: str
    decimal_places: int
    decimal_separator: str
    thousands_separator: str
    is_crypto: bool


class TimezoneOption(BaseModel):
    name: str        # IANA name e.g. "Asia/Tehran"
    label: str       # short display label e.g. "Tehran"


class AccountTypeOption(BaseModel):
    value: str
    icon: str


class ConfigOut(BaseModel):
    currencies: list[CurrencyOption]
    timezones: list[TimezoneOption]
    account_types: list[AccountTypeOption]
    calendars: list[str]


ACCOUNT_TYPE_ICONS: dict[AccountType, str] = {
    AccountType.CASH: "fa-money-bill-wave",
    AccountType.CARD: "fa-credit-card",
    AccountType.BANK: "fa-building-columns",
    AccountType.E_WALLET: "fa-mobile-screen",
    AccountType.CREDIT: "fa-credit-card",
    AccountType.INVESTMENT: "fa-chart-line",
    AccountType.SAVINGS: "fa-piggy-bank",
}


@router.get("/config", response_model=ConfigOut)
async def get_config() -> ConfigOut:
    ctx = load_app_context()
    return ConfigOut(
        currencies=[
            CurrencyOption(
                code=c.code,
                name=c.name,
                symbol=c.symbol,
                symbol_position=c.symbol_position,
                decimal_places=c.decimal_places,
                decimal_separator=c.decimal_separator,
                thousands_separator=c.thousands_separator,
                is_crypto=c.is_crypto,
            )
            for c in ctx.currencies.enabled()
        ],
        timezones=[
            TimezoneOption(name=name, label=label)
            for name, label in POPULAR_TIMEZONES
        ],
        account_types=[
            AccountTypeOption(value=at.value, icon=ACCOUNT_TYPE_ICONS[at])
            for at in AccountType
        ],
        calendars=["gregorian", "jalali", "hijri"],
    )
