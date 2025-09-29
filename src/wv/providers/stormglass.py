"""Stormglass 예보 어댑터. | Stormglass forecast adapter."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from ..core.models import ForecastPoint
from .base import MarineProvider, ProviderError


class StormglassProvider(MarineProvider):
    """Stormglass API 어댑터. | Stormglass API adapter."""

    def __init__(
        self, api_key: str | None = None, endpoint: str | None = None, timeout: float = 10.0
    ) -> None:
        super().__init__("Stormglass", timeout=timeout)
        self.api_key = api_key or os.getenv("STORMGLASS_API_KEY")
        env_endpoint = os.getenv("STORMGLASS_ENDPOINT")
        self.endpoint = endpoint or env_endpoint or "https://api.stormglass.io/v2/weather/point"

    def fetch_forecast(
        self, *, lat: float, lon: float, hours: int
    ) -> List[ForecastPoint]:  # pragma: no cover - external API
        """Stormglass에서 예보 수집. | Fetch forecast from Stormglass."""

        if not self.api_key:
            raise ProviderError("config", "Stormglass API key missing")

        params: dict[str, str | float | int | bool | None] = {
            "lat": lat,
            "lng": lon,
            "params": "waveHeight,windSpeed,windDirection,swellHeight,swellPeriod,swellDirection",
            "start": datetime.now(timezone.utc).isoformat(),
            "end": (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(),
        }

        headers: dict[str, str] = {"Authorization": self.api_key}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.endpoint, params=params, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - network
            raise ProviderError("timeout", "Stormglass timeout") from exc
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network
            if exc.response.status_code == 429:
                raise ProviderError("quota", "Stormglass quota reached") from exc
            raise ProviderError("http", f"Stormglass status {exc.response.status_code}") from exc

        body = response.json()
        hours_data = body.get("hours", [])
        points: List[ForecastPoint] = []
        for item in hours_data:
            values = {
                "hs": item.get("waveHeight", {}).get("sg"),
                "wind_speed": item.get("windSpeed", {}).get("sg"),
                "wind_dir": item.get("windDirection", {}).get("sg"),
                "swell_height": item.get("swellHeight", {}).get("sg"),
                "swell_period": item.get("swellPeriod", {}).get("sg"),
                "swell_dir": item.get("swellDirection", {}).get("sg"),
            }
            point = MarineProvider._build_point(
                {
                    **values,
                    "time": item.get("time"),
                    "tp": None,
                    "dp": values.get("swell_dir"),
                },
                time_key="time",
                lat=lat,
                lon=lon,
            )
            points.append(point)
        return points
