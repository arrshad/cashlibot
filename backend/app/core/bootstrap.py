"""Loads and validates YAML configs once at process startup."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from app.core.ai_providers import AIProvidersConfig
from app.core.app_config import AppConfig
from app.core.config import CONFIG_DIR
from app.core.currencies import CurrencyFormatter, CurrencyRegistry

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppContext:
    currencies: CurrencyRegistry
    currency_formatter: CurrencyFormatter
    ai_providers: AIProvidersConfig
    app: AppConfig


@lru_cache(maxsize=1)
def load_app_context() -> AppContext:
    currencies = CurrencyRegistry.load(CONFIG_DIR / "currencies.yaml")
    ai_providers = AIProvidersConfig.load(CONFIG_DIR / "ai_providers.yaml")
    app = AppConfig.load(CONFIG_DIR / "app.yaml")

    log.info(
        "config loaded: %d currencies enabled, AI provider '%s'",
        len(currencies.enabled_codes()),
        ai_providers.active_name,
    )

    return AppContext(
        currencies=currencies,
        currency_formatter=CurrencyFormatter(currencies),
        ai_providers=ai_providers,
        app=app,
    )
