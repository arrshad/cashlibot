"""AI provider config, loaded from `config/ai_providers.yaml`."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import ConfigError

ProviderType = Literal["openai", "openai_compatible", "anthropic", "ollama"]


class AIProviderDef(BaseModel):
    type: ProviderType
    model: str
    api_key_env: str | None = None
    base_url: str | None = None
    max_tokens: int = Field(default=2048, gt=0)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class AIProvidersConfig:
    def __init__(self, active: str, providers: dict[str, AIProviderDef]) -> None:
        self.active_name = active
        self.providers = providers

    @classmethod
    def load(cls, path: Path) -> "AIProvidersConfig":
        if not path.exists():
            raise ConfigError(f"ai_providers.yaml not found at {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigError("ai_providers.yaml must be a mapping")

        active = raw.get("active_provider")
        providers_raw = raw.get("providers")
        if not active or not isinstance(providers_raw, dict):
            raise ConfigError(
                "ai_providers.yaml must define 'active_provider' and 'providers'"
            )

        providers: dict[str, AIProviderDef] = {}
        for name, data in providers_raw.items():
            try:
                providers[name] = AIProviderDef(**data)
            except ValidationError as exc:
                raise ConfigError(f"invalid AI provider '{name}': {exc}") from exc

        if active not in providers:
            raise ConfigError(
                f"active_provider '{active}' is not defined in providers"
            )

        return cls(active, providers)

    @property
    def active(self) -> AIProviderDef:
        return self.providers[self.active_name]
