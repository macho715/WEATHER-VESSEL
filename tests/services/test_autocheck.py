from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from wv.core.models import ForecastPoint
from wv.services.autocheck import AutoCheckScheduler


class DummyService:
    def __init__(self, points: List[ForecastPoint]) -> None:
        self.points = points
        self.calls = 0

    def get_forecast(self, lat: float, lon: float, hours: int = 48):
        self.calls += 1
        return self.points


class DummyNotifier:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def send_all(self, title: str, message: str, dry_run: bool = False) -> None:
        if not dry_run:
            self.messages.append(f"{title}|{message}")


def _point() -> ForecastPoint:
    return ForecastPoint(
        time=datetime(2024, 3, 1, 2, 0, tzinfo=timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=1.8,
        tp=10.0,
        dp=180.0,
        wind_speed=18.0,
        wind_dir=120.0,
        swell_height=1.5,
        swell_period=11.0,
        swell_direction=200.0,
    )


def test_autocheck_runs_at_scheduled_time() -> None:
    service = DummyService([_point()])
    notifier = DummyNotifier()
    scheduler = AutoCheckScheduler(
        marine_service=service,
        notifier=notifier,
        routes={"MW4-AGI": (24.3488, 54.4651)},
    )
    now = datetime(2024, 3, 1, 2, 0, tzinfo=timezone.utc)  # 06:00 Asia/Dubai
    scheduler.run_pending(now=now)
    assert notifier.messages
    assert "MW4-AGI" in notifier.messages[0]


def test_autocheck_skips_non_window() -> None:
    service = DummyService([_point()])
    notifier = DummyNotifier()
    scheduler = AutoCheckScheduler(
        marine_service=service,
        notifier=notifier,
        routes={"MW4-AGI": (24.3488, 54.4651)},
    )
    now = datetime(2024, 3, 1, 5, 0, tzinfo=timezone.utc)  # 09:00 Asia/Dubai
    scheduler.run_pending(now=now)
    assert not notifier.messages
