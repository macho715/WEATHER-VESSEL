"""NOAA WaveWatch III 프로바이더. | NOAA WaveWatch III provider."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx

from wv.core.models import ForecastPoint
from wv.providers.base import (
    MarineProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


class NoaaWaveWatchProvider(MarineProvider):
    """NOAA WW3 API 어댑터. | NOAA WW3 API adapter."""

    name = "noaa_ww3"

    def __init__(
        self,
        endpoint: Optional[str] | None = None,
        client: Optional[httpx.Client] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.endpoint: str = (
            endpoint
            or os.getenv("NOAA_WW3_ENDPOINT", "https://nomads.ncep.noaa.gov/api/noaa_ww3")
            or "https://nomads.ncep.noaa.gov/api/noaa_ww3"
        )
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            client = getattr(self, "_client", None)
            if client is not None:
                client.close()

    def fetch(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """NOAA WaveWatch III 예측 조회. | Fetch NOAA WaveWatch III forecast."""
        params = {"lat": f"{lat:.4f}", "lon": f"{lon:.4f}", "hours": str(hours)}
        try:
            response = self._client.get(self.endpoint, params=params)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("NOAA WW3 request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"NOAA WW3 request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitError("NOAA WW3 rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderError(f"NOAA WW3 server error {response.status_code}")
        if response.status_code != 200:
            raise ProviderError(f"NOAA WW3 unexpected status {response.status_code}")

        payload = response.json()
        records = payload.get("data", [])
        points: List[ForecastPoint] = []
        for record in records:
            time_str = record.get("time")
            if time_str is None:
                continue
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
                    hs=_maybe_float(record.get("hs")),
                    tp=_maybe_float(record.get("tp")),
                    dp=_maybe_float(record.get("dp")),
                    wind_speed=_maybe_float(record.get("wind")),
                    wind_dir=_maybe_float(record.get("wind_dir")),
                    swell_height=_maybe_float(record.get("swell_hs")),
                    swell_period=_maybe_float(record.get("swell_tp")),
                    swell_direction=_maybe_float(record.get("swell_dir")),
                )
            )
        return points


def _maybe_float(value: Any) -> Optional[float]:
    """값을 부동소수로 변환. | Convert value to float."""
    if isinstance(value, (int, float, str)):
        return float(value)
    return None
