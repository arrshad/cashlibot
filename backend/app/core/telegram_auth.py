"""Verify Telegram WebApp `initData` strings using HMAC-SHA256.

See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qs


class InvalidInitData(Exception):
    """Raised when initData is missing, malformed, tampered with, or expired."""


@dataclass(frozen=True)
class InitDataUser:
    id: int
    username: str | None
    first_name: str
    last_name: str | None
    language_code: str | None

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name or self.username or str(self.id)


@dataclass(frozen=True)
class ParsedInitData:
    user: InitDataUser
    auth_date: int


def validate_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 86_400,
) -> ParsedInitData:
    """Verify the HMAC signature on a Telegram WebApp initData string.

    Raises `InvalidInitData` on any failure. On success, returns the parsed user.
    """
    if not init_data:
        raise InvalidInitData("empty init data")
    if not bot_token:
        raise InvalidInitData("bot token not configured")

    parsed = {
        k: v[0] for k, v in parse_qs(init_data, keep_blank_values=True).items()
    }
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("missing hash")

    data_check_string = "\n".join(
        f"{k}={parsed[k]}" for k in sorted(parsed.keys())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise InvalidInitData("hash mismatch")

    auth_date_raw = parsed.get("auth_date")
    if not auth_date_raw:
        raise InvalidInitData("missing auth_date")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InvalidInitData("invalid auth_date") from exc
    if time.time() - auth_date > max_age_seconds:
        raise InvalidInitData("init data expired")

    user_raw = parsed.get("user")
    if not user_raw:
        raise InvalidInitData("missing user")
    try:
        user_data = json.loads(user_raw)
    except ValueError as exc:
        raise InvalidInitData("invalid user json") from exc

    try:
        user = InitDataUser(
            id=int(user_data["id"]),
            username=user_data.get("username"),
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code"),
        )
    except (KeyError, ValueError) as exc:
        raise InvalidInitData(f"malformed user: {exc}") from exc

    return ParsedInitData(user=user, auth_date=auth_date)
