"""Translation lookup. Loads `en.yaml` and `fa.yaml` at startup."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.core.exceptions import ConfigError

log = logging.getLogger(__name__)

I18N_DIR = Path(__file__).parent
SUPPORTED = ("en", "fa")
DEFAULT_LANG = "en"


def _resolve(d: dict, key: str) -> Any:
    """Walk a dotted key path through a nested dict."""
    cursor: Any = d
    for part in key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


class I18N:
    def __init__(self, translations: dict[str, dict]) -> None:
        for lang in SUPPORTED:
            if lang not in translations:
                raise ConfigError(f"i18n: missing translations for '{lang}'")
        self._t = translations

    def t(self, lang: str, key: str, **fmt: Any) -> str:
        """Look up `key` in `lang`, falling back to English, then to the key itself."""
        value = _resolve(self._t.get(lang, {}), key)
        if value is None:
            value = _resolve(self._t[DEFAULT_LANG], key)
        if value is None:
            log.warning("missing i18n key: %s", key)
            return key
        if fmt:
            return str(value).format(**fmt)
        return str(value)


@lru_cache(maxsize=1)
def get_i18n() -> I18N:
    translations: dict[str, dict] = {}
    for lang in SUPPORTED:
        path = I18N_DIR / f"{lang}.yaml"
        if not path.exists():
            raise ConfigError(f"i18n file not found: {path}")
        translations[lang] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return I18N(translations)
