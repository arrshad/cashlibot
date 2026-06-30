"""Tunable app behavior, loaded from `config/app.yaml`."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import ConfigError


class CreditsConfig(BaseModel):
    signup_bonus: int = Field(ge=0)
    referral_bonus: int = Field(ge=0)
    friend_add_bonus: int = Field(ge=0)
    stars_to_credits_rate: int = Field(gt=0)
    ai_agent_call_cost: int = Field(ge=0)
    ai_memory_cost: int = Field(ge=0)
    ai_report_insight_cost: int = Field(ge=0)


class BotConfig(BaseModel):
    max_inline_choices: int = Field(gt=0, le=10)
    conversation_history_max: int = Field(gt=0, le=100)


class GamificationConfig(BaseModel):
    xp_per_transaction: int = Field(ge=0)
    xp_per_budget_kept: int = Field(ge=0)
    xp_per_streak_day: int = Field(ge=0)
    xp_per_goal_reached: int = Field(ge=0)
    level_xp_base: int = Field(gt=0)


class AppConfig(BaseModel):
    credits: CreditsConfig
    bot: BotConfig
    gamification: GamificationConfig

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            raise ConfigError(f"app.yaml not found at {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigError("app.yaml must be a mapping")

        try:
            return cls(**raw)
        except ValidationError as exc:
            raise ConfigError(f"invalid app.yaml: {exc}") from exc
