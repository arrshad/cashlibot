"""LangChain chat-model factory driven by ai_providers.yaml + env."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from app.core.ai_providers import AIProviderDef, AIProvidersConfig
from app.core.config import Settings
from app.core.exceptions import ConfigError


class AIUnavailableError(RuntimeError):
    """Raised when the AI subsystem can't be used yet (missing API key, etc.)."""


def build_chat_model(cfg: AIProvidersConfig, settings: Settings) -> BaseChatModel:
    """Instantiate a LangChain chat model for the currently active provider."""
    provider = cfg.active
    key = _resolve_api_key(provider, settings)

    if provider.type in ("openai", "openai_compatible"):
        from langchain_openai import ChatOpenAI

        _require_key(provider, key)
        kwargs: dict = {
            "model": provider.model,
            "api_key": key,
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens,
        }
        if provider.type == "openai_compatible" and provider.base_url:
            kwargs["base_url"] = provider.base_url
        return ChatOpenAI(**kwargs)

    if provider.type == "anthropic":
        from langchain_anthropic import ChatAnthropic

        _require_key(provider, key)
        return ChatAnthropic(
            model_name=provider.model,
            api_key=key,
            temperature=provider.temperature,
            max_tokens=provider.max_tokens,
            timeout=None,
            stop=None,
        )

    if provider.type == "ollama":
        # Kept out of requirements.txt for now so the base image stays lean.
        # If the user selects ollama, they can pip install langchain-ollama.
        try:
            from langchain_ollama import ChatOllama  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise AIUnavailableError(
                "langchain-ollama is not installed. "
                "Add it to requirements.txt or switch providers in ai_providers.yaml."
            ) from exc
        return ChatOllama(
            model=provider.model,
            base_url=provider.base_url,
            temperature=provider.temperature,
            num_predict=provider.max_tokens,
        )

    raise ConfigError(f"unsupported provider type: {provider.type}")


def _resolve_api_key(provider: AIProviderDef, settings: Settings) -> str | None:
    if not provider.api_key_env:
        return None
    return getattr(settings, provider.api_key_env.lower(), None) or None


def _require_key(provider: AIProviderDef, key: str | None) -> None:
    if not key:
        raise AIUnavailableError(
            f"AI provider '{provider.model}' needs {provider.api_key_env}. "
            "Set it in .env and restart the bot."
        )
