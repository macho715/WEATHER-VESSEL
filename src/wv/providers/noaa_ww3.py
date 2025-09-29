"""NOAA WaveWatch III 어댑터. | NOAA WaveWatch III adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import httpx

from ..core.models import ForecastPoint
from .base import MarineProvider, ProviderError


class NoaaWaveWatchProvider(MarineProvider):
    """NOAA WW3 API 어댑터. | NOAA WW3 API adapter."""

    def __init__(self, endpoint: str | None = None, timeout: float = 10.0) -> None:
        super().__init__("NOAA WaveWatch III", timeout=timeout)
        self.endpoint = endpoint or "https://nomads.ncep.noaa.gov/cgi-bin/filter_ww3_multi.pl"

    def fetch_forecast(
        self, *, lat: float, lon: float, hours: int
    ) -> List[ForecastPoint]:  # pragma: no cover - external API
        """NOAA WW3 예보 수집. | Fetch forecast from NOAA WW3."""

        params: dict[str, str | float | int | bool | None] = {
            "var_WVHGT": "on",
            "var_DIRPW": "on",
            "var_WVDIR": "on",
            "var_UGRD": "on",
            "var_VGRD": "on",
            "dir": "multi_1.202401/",
            "file": "multi_1.glo_30m.t00z.grib2",
            "subregion": f"lat_{lat}:{lat}:0.0&lon_{lon}:{lon}:0.0",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.endpoint, params=params)
                if response.status_code == 404:
                    raise ProviderError("unavailable", "NOAA data unavailable")
                response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - network
            raise ProviderError("timeout", "NOAA timeout") from exc
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network
            raise ProviderError("http", f"NOAA status {exc.response.status_code}") from exc

        # Simplified parsing placeholder
        now = datetime.now(timezone.utc)
        points = [
            ForecastPoint(
                time=now,
                lat=lat,
                lon=lon,
                hs=2.0,
                tp=8.0,
                dp=180.0,
                wind_speed=18.0,
                wind_dir=200.0,
                swell_height=1.8,
                swell_period=9.0,
                swell_dir=185.0,
            )
        ]
        return points
