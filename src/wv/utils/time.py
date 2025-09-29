"""시간 유틸리티. Time utilities."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

ASIA_DUBAI = ZoneInfo("Asia/Dubai")


def now_dubai() -> dt.datetime:
    """두바이 현재 시각. Current time in Dubai."""

    return dt.datetime.now(dt.timezone.utc).astimezone(ASIA_DUBAI)


def to_utc(value: dt.datetime) -> dt.datetime:
    """UTC로 변환. Convert to UTC."""

    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone aware")
    return value.astimezone(dt.timezone.utc)


def ensure_tz(value: dt.datetime, tz: ZoneInfo) -> dt.datetime:
    """타임존 설정. Attach timezone."""

    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


__all__ = ["ASIA_DUBAI", "now_dubai", "to_utc", "ensure_tz"]
