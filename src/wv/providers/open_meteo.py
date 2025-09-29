"""Open-Meteo Marine 어댑터. | Open-Meteo marine adapter."""

from __future__ import annotations

from typing import List

import httpx

from ..core.models import ForecastPoint
from .base import MarineProvider, ProviderError


class OpenMeteoMarineProvider(MarineProvider):
    """Open-Meteo 해양 API 어댑터. | Open-Meteo marine API adapter."""

    def __init__(self, endpoint: str | None = None, timeout: float = 10.0) -> None:
        super().__init__("Open-Meteo Marine", timeout=timeout)
        self.endpoint = endpoint or "https://marine-api.open-meteo.com/v1/marine"

    def fetch_forecast(
        self, *, lat: float, lon: float, hours: int
    ) -> List[ForecastPoint]:  # pragma: no cover - external API
        """Open-Meteo 예보 수집. | Fetch forecast from Open-Meteo."""

        params: dict[str, str | float | int | bool | None] = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wind_speed,wind_direction,wind_wave_height,wind_wave_period",
            "length": hours,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.endpoint, params=params)
                response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - network
            raise ProviderError("timeout", "Open-Meteo timeout") from exc
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network
            if exc.response.status_code == 429:
                raise ProviderError("quota", "Open-Meteo quota reached") from exc
            raise ProviderError("http", f"Open-Meteo status {exc.response.status_code}") from exc

        data = response.json()
        times = data.get("hourly", {}).get("time", [])
        wave_height = data.get("hourly", {}).get("wave_height", [])
        wind_speed = data.get("hourly", {}).get("wind_speed", [])
        wind_dir = data.get("hourly", {}).get("wind_direction", [])
        swell_height = data.get("hourly", {}).get("wind_wave_height", [])
        swell_period = data.get("hourly", {}).get("wind_wave_period", [])

        points: List[ForecastPoint] = []
        for idx, ts in enumerate(times):
            values = {
                "hs": wave_height[idx] if idx < len(wave_height) else None,
                "wind_speed": wind_speed[idx] if idx < len(wind_speed) else None,
                "wind_dir": wind_dir[idx] if idx < len(wind_dir) else None,
                "swell_height": swell_height[idx] if idx < len(swell_height) else None,
                "swell_period": swell_period[idx] if idx < len(swell_period) else None,
            }
            point = MarineProvider._build_point(
                {
                    **values,
                    "time": ts,
                    "tp": values.get("swell_period"),
                    "dp": values.get("wind_dir"),
                },
                time_key="time",
                lat=lat,
                lon=lon,
            )
            points.append(point)
        return points
