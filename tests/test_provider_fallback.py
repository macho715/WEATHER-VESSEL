from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import pytest

from wv.core.models import ForecastPoint
from wv.providers.base import MarineProvider, ProviderError
from wv.providers.manager import ProviderManager


class _FailingProvider(MarineProvider):
    def __init__(self, name: str, code: str) -> None:
        super().__init__(name)
        self.code = code
        self.calls = 0

    def fetch_forecast(self, *, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        self.calls += 1
        raise ProviderError(self.code, f"{self.code} failure")


class _StaticProvider(MarineProvider):
    def __init__(self, name: str, points: Iterable[ForecastPoint]) -> None:
        super().__init__(name)
        self.points = list(points)
        self.calls = 0

    def fetch_forecast(self, *, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        self.calls += 1
        return self.points


@pytest.fixture()
def sample_points() -> list[ForecastPoint]:
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        ForecastPoint(
            time=base_time,
            lat=lat,
            lon=lon,
            hs=1.5,
            tp=8.0,
            dp=120.0,
            wind_speed=15.0,
            wind_dir=180.0,
            swell_height=1.4,
            swell_period=9.0,
            swell_dir=190.0,
        )
        for lat, lon in [(24.3, 54.4), (24.4, 54.5)]
    ]


def test_manager_falls_back_and_caches(tmp_path: Path, sample_points: list[ForecastPoint]) -> None:
    cache_dir = tmp_path / "cache"
    manager = ProviderManager(
        providers=[
            _FailingProvider("Stormglass", code="timeout"),
            _FailingProvider("Open-Meteo", code="quota"),
            _StaticProvider("NOAA", points=sample_points),
        ],
        cache_dir=cache_dir,
        cache_ttl_seconds=3600,
    )

    result = manager.fetch_with_fallback(lat=24.3, lon=54.4, hours=48)
    assert result == sample_points

    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 1

    # second call should hit cache and avoid calling providers again
    for provider in manager.providers:
        if hasattr(provider, "calls"):
            provider.calls = 0

    cached_result = manager.fetch_with_fallback(lat=24.3, lon=54.4, hours=48)
    assert cached_result == sample_points
    assert all(getattr(provider, "calls", 0) == 0 for provider in manager.providers)
