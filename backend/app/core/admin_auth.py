"""Signed JWT for the admin dashboard.

The bot's `/admin` command mints one of these for `User.is_admin` users and
DMs the URL. FastAPI's admin routes verify the same signature.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt

_ALGO = "HS256"
_DEFAULT_TTL_SECONDS = 24 * 60 * 60


class InvalidAdminToken(Exception):
    """Raised when the presented JWT is missing, malformed, or expired."""


@dataclass(frozen=True)
class AdminClaims:
    telegram_id: int
    issued_at: int
    expires_at: int


def create_admin_token(
    *, telegram_id: int, secret: str, ttl_seconds: int = _DEFAULT_TTL_SECONDS
) -> str:
    if not secret:
        raise InvalidAdminToken("ADMIN_JWT_SECRET is not configured")
    now = int(time.time())
    payload = {
        "sub": str(telegram_id),
        "iat": now,
        "exp": now + ttl_seconds,
        "role": "admin",
    }
    return jwt.encode(payload, secret, algorithm=_ALGO)


def verify_admin_token(token: str, secret: str) -> AdminClaims:
    if not token:
        raise InvalidAdminToken("empty token")
    if not secret:
        raise InvalidAdminToken("ADMIN_JWT_SECRET is not configured")
    try:
        decoded = jwt.decode(token, secret, algorithms=[_ALGO])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidAdminToken("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidAdminToken(f"invalid token: {exc}") from exc

    if decoded.get("role") != "admin":
        raise InvalidAdminToken("token is not for admin role")
    try:
        telegram_id = int(decoded["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidAdminToken("token missing sub") from exc

    return AdminClaims(
        telegram_id=telegram_id,
        issued_at=int(decoded.get("iat", 0)),
        expires_at=int(decoded.get("exp", 0)),
    )
