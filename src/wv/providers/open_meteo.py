"""Open-Meteo 해양 데이터 어댑터. | Open-Meteo marine data adapter."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence

import httpx

from wv.core.models import ForecastPoint
from wv.providers.base import (
    MarineProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


class OpenMeteoMarineProvider(MarineProvider):
    """Open-Meteo 마린 API 어댑터. | Open-Meteo marine API adapter."""

    name = "open_meteo"

    def __init__(
        self,
        endpoint: Optional[str] | None = None,
        client: Optional[httpx.Client] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.endpoint: str = (
            endpoint
            or os.getenv("OPEN_METEO_ENDPOINT", "https://marine-api.open-meteo.com/v1/marine")
            or "https://marine-api.open-meteo.com/v1/marine"
        )
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            client = getattr(self, "_client", None)
            if client is not None:
                client.close()

    def fetch(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """Open-Meteo에서 예측을 조회. | Fetch forecast from Open-Meteo."""
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "hourly": "wave_height,wind_speed,wind_direction,wave_direction,wave_period",
            "forecast_hours": str(hours),
        }
        try:
            response = self._client.get(self.endpoint, params=params)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Open-Meteo request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Open-Meteo request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitError("Open-Meteo rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"Open-Meteo server error {response.status_code}")
        if response.status_code != 200:
            raise ProviderError(f"Open-Meteo unexpected status {response.status_code}")

        payload = response.json()
        hourly = payload.get("hourly", {})
        times: Sequence[str] = hourly.get("time", [])
        heights: Sequence[Any] = hourly.get("wave_height", [])
        wind_speeds: Sequence[Any] = hourly.get("wind_speed", [])
        wind_dirs: Sequence[Any] = hourly.get("wind_direction", [])
        wave_dirs: Sequence[Any] = hourly.get("wave_direction", [])
        wave_periods: Sequence[Any] = hourly.get("wave_period", [])

        points: List[ForecastPoint] = []
        for index, time_str in enumerate(times):
            try:
                timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            points.append(
                ForecastPoint(
                    time=timestamp,
                    lat=lat,
                    lon=lon,
                    hs=_safe_float(heights, index),
                    tp=_safe_float(wave_periods, index),
                    dp=_safe_float(wave_dirs, index),
                    wind_speed=_safe_float(wind_speeds, index),
                    wind_dir=_safe_float(wind_dirs, index),
                    swell_height=None,
                    swell_period=_safe_float(wave_periods, index),
                    swell_direction=_safe_float(wave_dirs, index),
                )
            )
        return points


def _safe_float(values: Sequence[Any], index: int) -> Optional[float]:
    """배열에서 안전하게 부동소수 추출. | Safely extract float from list."""
    if index >= len(values):
        return None
    value = values[index]
    if isinstance(value, (int, float, str)):
        return float(value)
    return None
