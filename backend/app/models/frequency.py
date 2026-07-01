"""Shared Frequency enum used by reminders and (later) recurring transactions."""

from __future__ import annotations

from enum import Enum


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
