import datetime as dt
from typing import Iterable

import pytest

from wv.core.models import ForecastPoint
from wv.providers.base import BaseProvider, ProviderError
from wv.providers.manager import ProviderManager
from wv.utils.cache import DiskCache


class _FailingProvider(BaseProvider):
    """실패 공급자 시뮬레이션. Simulate provider failure."""

    def __init__(self, name: str, exc: Exception) -> None:
        self._name = name
        self._exc = exc

    @property
    def name(self) -> str:
        return self._name

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        raise self._exc


class _SuccessProvider(BaseProvider):
    """성공 공급자 시뮬레이션. Simulate provider success."""

    def __init__(self, name: str, points: list[ForecastPoint]) -> None:
        self._name = name
        self._points = points

    @property
    def name(self) -> str:
        return self._name

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        return self._points


def _sample_points() -> list[ForecastPoint]:
    base = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
    return [
        ForecastPoint(
            time=base,
            lat=24.3,
            lon=54.4,
            hs=1.2,
            tp=6.0,
            dp=120.0,
            wind_speed=10.0,
            wind_dir=90.0,
            swell_height=1.0,
            swell_period=8.0,
            swell_direction=110.0,
        )
    ]


def test_provider_fallback_and_cache(tmp_path) -> None:
    cache_dir = tmp_path / "cache"
    cache = DiskCache(root=cache_dir)
    points = _sample_points()
    manager = ProviderManager(
        providers=[
            _FailingProvider("stormglass", ProviderError("quota exceeded")),
            _SuccessProvider("open-meteo", points),
        ],
        cache=cache,
    )

    result = manager.get_forecast(lat=24.4, lon=54.7, hours=6)
    assert list(result) == points

    # When all providers fail, the cached response should be returned.
    failing_manager = ProviderManager(
        providers=[
            _FailingProvider("stormglass", ProviderError("quota exceeded")),
            _FailingProvider("open-meteo", ProviderError("timeout")),
        ],
        cache=cache,
    )
    cached = failing_manager.get_forecast(lat=24.4, lon=54.7, hours=6)
    assert list(cached) == points


def test_provider_cache_stale(tmp_path) -> None:
    cache_dir = tmp_path / "cache"
    cache = DiskCache(root=cache_dir, ttl=dt.timedelta(seconds=1))
    points = _sample_points()
    manager = ProviderManager(
        providers=[_SuccessProvider("stormglass", points)],
        cache=cache,
    )
    manager.get_forecast(lat=24.4, lon=54.7, hours=6)

    # Advance time beyond TTL by monkeypatching now.
    future = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=5)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("wv.utils.cache.utcnow", lambda: future)
        with pytest.raises(ProviderError):
            manager.get_forecast(lat=24.4, lon=54.7, hours=6, use_cache_only=True)
