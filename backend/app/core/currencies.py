"""Currency registry and formatter, loaded from `config/currencies.yaml`."""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import ConfigError

CURRENCY_CODE_RE = re.compile(r"^[A-Z]{2,5}$")


class CurrencyDef(BaseModel):
    code: str
    name: str
    symbol: str = Field(min_length=1, max_length=10)
    symbol_position: Literal["before", "after"]
    decimal_places: int = Field(ge=0, le=8)
    decimal_separator: str = Field(min_length=1, max_length=1)
    thousands_separator: str = Field(min_length=0, max_length=1)
    is_crypto: bool = False
    enabled: bool = True

    @field_validator("code")
    @classmethod
    def _code_format(cls, v: str) -> str:
        if not CURRENCY_CODE_RE.match(v):
            raise ValueError("must be 2–5 uppercase letters")
        return v


class CurrencyRegistry:
    """Loaded once at process startup. All currency lookups go through it."""

    def __init__(self, currencies: dict[str, CurrencyDef]) -> None:
        self._all: dict[str, CurrencyDef] = currencies
        self._enabled: dict[str, CurrencyDef] = {
            code: c for code, c in currencies.items() if c.enabled
        }

    @classmethod
    def load(cls, path: Path) -> "CurrencyRegistry":
        if not path.exists():
            raise ConfigError(f"currencies.yaml not found at {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "currencies" not in raw:
            raise ConfigError("currencies.yaml must contain a top-level 'currencies' map")

        currencies: dict[str, CurrencyDef] = {}
        for code, data in raw["currencies"].items():
            try:
                currencies[code] = CurrencyDef(code=code, **data)
            except ValidationError as exc:
                raise ConfigError(f"invalid currency '{code}': {exc}") from exc

        if not currencies:
            raise ConfigError("currencies.yaml defines no currencies")
        if not any(c.enabled for c in currencies.values()):
            raise ConfigError("currencies.yaml has no enabled currencies")

        return cls(currencies)

    def get(self, code: str) -> CurrencyDef:
        try:
            return self._all[code]
        except KeyError as exc:
            raise ConfigError(f"unknown currency '{code}'") from exc

    def is_enabled(self, code: str) -> bool:
        return code in self._enabled

    def enabled_codes(self) -> list[str]:
        return list(self._enabled.keys())

    def enabled(self) -> list[CurrencyDef]:
        return list(self._enabled.values())


class CurrencyFormatter:
    """Format Decimal amounts according to the rules in a CurrencyDef."""

    def __init__(self, registry: CurrencyRegistry) -> None:
        self._registry = registry

    def format(self, amount: Decimal, code: str) -> str:
        currency = self._registry.get(code)
        quantized = amount.quantize(Decimal(10) ** -currency.decimal_places)
        sign = "-" if quantized < 0 else ""
        whole, _, frac = format(abs(quantized), "f").partition(".")

        if currency.thousands_separator:
            whole = self._with_thousands(whole, currency.thousands_separator)

        if currency.decimal_places > 0:
            frac = frac.ljust(currency.decimal_places, "0")[: currency.decimal_places]
            number = f"{whole}{currency.decimal_separator}{frac}"
        else:
            number = whole

        if currency.symbol_position == "before":
            return f"{sign}{currency.symbol}{number}"
        return f"{sign}{number} {currency.symbol}"

    @staticmethod
    def _with_thousands(whole: str, sep: str) -> str:
        if len(whole) <= 3:
            return whole
        # Walk from the right inserting a separator every 3 digits.
        parts: list[str] = []
        for i, ch in enumerate(reversed(whole)):
            if i > 0 and i % 3 == 0:
                parts.append(sep)
            parts.append(ch)
        return "".join(reversed(parts))
