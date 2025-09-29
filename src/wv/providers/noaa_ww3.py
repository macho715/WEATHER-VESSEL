"""NOAA WaveWatch III 공급자. NOAA WaveWatch III provider."""

from __future__ import annotations

import datetime as dt
import os
from typing import Iterable

from wv.core.models import ForecastPoint
from wv.providers.base import BaseProvider, ProviderError
from wv.utils.http import request_json


class NoaaWaveWatchProvider(BaseProvider):
    """NOAA WW3 JSON 어댑터. NOAA WW3 JSON adapter."""

    def __init__(self) -> None:
        self._endpoint = os.getenv("WV_NOAA_WW3_ENDPOINT")

    @property
    def name(self) -> str:
        """공급자 이름. Provider name."""

        return "noaa-ww3"

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        """예보 조회 수행. Retrieve forecast payload."""

        if not self._endpoint:
            raise ProviderError("NOAA endpoint not configured")
        params = {"lat": lat, "lon": lon, "hours": hours}
        payload = request_json(
            "GET",
            self._endpoint,
            params=params,
            timeout=self.timeout,
            retries=self.max_retries,
            backoff_factor=self.backoff_factor,
        )
        data = payload.get("data")
        if not data:
            raise ProviderError("NOAA payload missing data")
        points: list[ForecastPoint] = []
        for entry in data:
            time_raw = entry.get("time")
            if not time_raw:
                continue
            time = dt.datetime.fromisoformat(str(time_raw).replace("Z", "+00:00"))
            points.append(
                ForecastPoint(
                    time=time,
                    lat=lat,
                    lon=lon,
                    hs=float(entry.get("hs", 0.0)),
                    tp=float(entry.get("tp", 0.0)),
                    dp=float(entry.get("dp", 0.0)),
                    wind_speed=float(entry.get("wind_speed", 0.0)),
                    wind_dir=float(entry.get("wind_dir", 0.0)),
                    swell_height=float(entry.get("swell_height", entry.get("hs", 0.0))),
                    swell_period=float(entry.get("swell_period", entry.get("tp", 0.0))),
                    swell_direction=float(entry.get("swell_direction", entry.get("dp", 0.0))),
                )
            )
        if not points:
            raise ProviderError("NOAA WW3 returned no usable records")
        return points


__all__ = ["NoaaWaveWatchProvider"]
