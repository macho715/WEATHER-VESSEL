"""Stormglass 해양 데이터 프로바이더. | Stormglass marine data provider."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from wv.core.models import ForecastPoint
from wv.providers.base import (
    MarineProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


class StormglassProvider(MarineProvider):
    """Stormglass API 어댑터. | Stormglass API adapter."""

    name = "stormglass"

    def __init__(
        self,
        api_key: Optional[str] | None = None,
        endpoint: Optional[str] | None = None,
        client: Optional[httpx.Client] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key or os.getenv("STORMGLASS_API_KEY") or ""
        self.endpoint: str = (
            endpoint
            or os.getenv("STORMGLASS_ENDPOINT", "https://api.stormglass.io/v2/weather/point")
            or "https://api.stormglass.io/v2/weather/point"
        )
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            client = getattr(self, "_client", None)
            if client is not None:
                client.close()

    def fetch(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """Stormglass에서 예측을 조회. | Fetch forecast from Stormglass."""
        end_time = datetime.now(timezone.utc) + timedelta(hours=hours)
        params = {
            "lat": f"{lat:.4f}",
            "lng": f"{lon:.4f}",
            "params": "waveHeight,wavePeriod,waveDirection,windSpeed,windDirection",
            "start": datetime.now(timezone.utc).isoformat(),
            "end": end_time.isoformat(),
            "source": "sg",
        }
        headers = {"Authorization": self.api_key} if self.api_key else {}
        try:
            response = self._client.get(self.endpoint, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Stormglass request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Stormglass request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitError("Stormglass rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"Stormglass server error {response.status_code}")
        if response.status_code != 200:
            raise ProviderError(f"Stormglass unexpected status {response.status_code}")

        payload = response.json()
        hours_data = payload.get("hours", [])
        points: List[ForecastPoint] = []
        for item in hours_data:
            time_str = item.get("time")
            if time_str is None:
                continue
            try:
                timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            points.append(
                ForecastPoint(
                    time=timestamp,
                    lat=lat,
                    lon=lon,
                    hs=_nested(item, "waveHeight"),
                    tp=_nested(item, "wavePeriod"),
                    dp=_nested(item, "waveDirection"),
                    wind_speed=_nested(item, "windSpeed"),
                    wind_dir=_nested(item, "windDirection"),
                    swell_height=_nested(item, "swellHeight"),
                    swell_period=_nested(item, "swellPeriod"),
                    swell_direction=_nested(item, "swellDirection"),
                )
            )
        return points


def _nested(data: Dict[str, Any], key: str) -> Optional[float]:
    """중첩된 sg 키를 추출. | Extract nested sg key."""
    value = data.get(key)
    if isinstance(value, dict):
        inner = value.get("sg")
        if isinstance(inner, (int, float, str)):
            return float(inner)
        return None
    if isinstance(value, (int, float, str)):
        return float(value)
    return None
