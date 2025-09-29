"""Copernicus Marine 어댑터. | Copernicus Marine adapter."""

from __future__ import annotations

import os
from typing import List

import httpx

from ..core.models import ForecastPoint
from .base import MarineProvider, ProviderError


class CopernicusMarineProvider(MarineProvider):
    """Copernicus Marine API 어댑터. | Copernicus Marine API adapter."""

    def __init__(
        self, api_key: str | None = None, endpoint: str | None = None, timeout: float = 10.0
    ) -> None:
        super().__init__("Copernicus Marine", timeout=timeout)
        self.api_key = api_key or os.getenv("COPERNICUS_API_KEY")
        env_endpoint = os.getenv("COPERNICUS_ENDPOINT")
        self.endpoint = endpoint or env_endpoint or "https://cmems.obs-mg.eu/api"

    def fetch_forecast(
        self, *, lat: float, lon: float, hours: int
    ) -> List[ForecastPoint]:  # pragma: no cover - external API
        """Copernicus 예보 수집. | Fetch forecast from Copernicus."""

        if not self.api_key:
            raise ProviderError("config", "Copernicus API key missing")

        params: dict[str, str | float | int | bool | None] = {
            "lat": lat,
            "lon": lon,
            "hours": hours,
        }
        headers: dict[str, str] = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.endpoint, params=params, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - network
            raise ProviderError("timeout", "Copernicus timeout") from exc
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network
            if exc.response.status_code == 429:
                raise ProviderError("quota", "Copernicus quota reached") from exc
            raise ProviderError("http", f"Copernicus status {exc.response.status_code}") from exc

        data = response.json().get("data", [])
        points: List[ForecastPoint] = []
        for item in data:
            point = MarineProvider._build_point(item, time_key="time", lat=lat, lon=lon)
            points.append(point)
        return points
