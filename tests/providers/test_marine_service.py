from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import httpx
import pytest

from wv.core.cache import CacheRepository
from wv.core.models import ForecastPoint
from wv.providers.base import ProviderError
from wv.providers.noaa_ww3 import NoaaWaveWatchProvider
from wv.providers.open_meteo import OpenMeteoMarineProvider
from wv.providers.stormglass import StormglassProvider
from wv.services.marine import MarineForecastService


def _make_client(response: httpx.Response) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


def test_service_uses_primary_provider(tmp_path) -> None:
    response = httpx.Response(
        status_code=200,
        json={
            "hours": [
                {
                    "time": "2024-03-01T00:00:00+00:00",
                    "waveHeight": {"sg": 1.2},
                    "wavePeriod": {"sg": 10.0},
                    "waveDirection": {"sg": 180.0},
                    "windSpeed": {"sg": 5.0},
                    "windDirection": {"sg": 90.0},
                }
            ]
        },
    )
    provider = StormglassProvider(api_key="test", client=_make_client(response))
    service = MarineForecastService(
        providers=[provider],
        cache=CacheRepository(base_path=tmp_path),
    )
    points = service.get_forecast(lat=24.3, lon=54.4, hours=6)
    assert len(points) == 1
    assert isinstance(points[0], ForecastPoint)
    assert points[0].hs == pytest.approx(1.2)


def test_service_falls_back_on_rate_limit(tmp_path) -> None:
    limited_provider = StormglassProvider(
        api_key="test",
        client=_make_client(httpx.Response(status_code=429)),
    )
    fallback_response = httpx.Response(
        status_code=200,
        json={
            "hourly": {
                "time": ["2024-03-01T00:00"],
                "wave_height": [1.5],
                "wind_speed": [12.0],
                "wind_direction": [135.0],
                "wave_period": [9.0],
                "wave_direction": [200.0],
            }
        },
    )
    fallback_provider = OpenMeteoMarineProvider(client=_make_client(fallback_response))
    service = MarineForecastService(
        providers=[limited_provider, fallback_provider],
        cache=CacheRepository(base_path=tmp_path),
    )
    points = service.get_forecast(lat=24.3, lon=54.4, hours=6)
    assert len(points) == 1
    assert points[0].hs == pytest.approx(1.5)


def test_service_returns_cache_when_all_fail(tmp_path) -> None:
    cache = CacheRepository(base_path=tmp_path)
    key = cache.make_key("stormglass", {"lat": 24.3, "lon": 54.4, "hours": 6})
    cached_point = ForecastPoint(
        time=datetime(2024, 3, 1, tzinfo=timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=1.8,
        tp=10.0,
        dp=190.0,
        wind_speed=14.0,
        wind_dir=100.0,
        swell_height=1.8,
        swell_period=10.0,
        swell_direction=200.0,
    )
    cache.store(
        key,
        payload=[cached_point.model_dump(mode="json")],
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
    )

    class BrokenProvider(StormglassProvider):
        def __init__(self) -> None:
            pass

        def fetch(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
            raise ProviderError("boom")

    service = MarineForecastService(
        providers=[
            BrokenProvider(),
            NoaaWaveWatchProvider(client=_make_client(httpx.Response(status_code=500))),
        ],
        cache=cache,
    )
    points = service.get_forecast(lat=24.3, lon=54.4, hours=6)
    assert len(points) == 1
    assert points[0].hs == pytest.approx(1.8)
