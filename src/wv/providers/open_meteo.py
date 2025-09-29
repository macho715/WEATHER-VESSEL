"""오픈 메테오 해양 공급자. Open-Meteo marine provider."""

from __future__ import annotations

import datetime as dt
import os
from typing import Iterable

from wv.core.models import ForecastPoint
from wv.providers.base import BaseProvider, ProviderError
from wv.utils.http import request_json


class OpenMeteoMarineProvider(BaseProvider):
    """오픈 메테오 API 래퍼. Wrapper for Open-Meteo API."""

    def __init__(self) -> None:
        self._endpoint = os.getenv(
            "WV_OPEN_METEO_ENDPOINT", "https://marine-api.open-meteo.com/v1/marine"
        )

    @property
    def name(self) -> str:
        """공급자 이름. Provider name."""

        return "open-meteo-marine"

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        """예보 조회 수행. Retrieve forecast payload."""

        hourly_params = [
            "wave_height",
            "wave_direction",
            "wave_period",
            "wind_speed_10m",
            "wind_direction_10m",
            "swell_wave_height",
            "swell_wave_direction",
            "swell_wave_period",
        ]
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(hourly_params),
            "length": hours,
        }
        payload = request_json(
            "GET",
            self._endpoint,
            params=params,
            timeout=self.timeout,
            retries=self.max_retries,
            backoff_factor=self.backoff_factor,
        )
        hourly = payload.get("hourly")
        if not hourly:
            raise ProviderError("Open-Meteo payload missing hourly data")
        times = list(hourly.get("time", []))
        wave_heights = list(hourly.get("wave_height", []))
        wave_dirs = list(hourly.get("wave_direction", []))
        wave_periods = list(hourly.get("wave_period", []))
        wind_speeds = list(hourly.get("wind_speed_10m", []))
        wind_dirs = list(hourly.get("wind_direction_10m", []))
        swell_heights = list(hourly.get("swell_wave_height", wave_heights))
        swell_dirs = list(hourly.get("swell_wave_direction", wave_dirs))
        swell_periods = list(hourly.get("swell_wave_period", wave_periods))

        points: list[ForecastPoint] = []
        for idx, time_raw in enumerate(times):
            time = dt.datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
            points.append(
                ForecastPoint(
                    time=time,
                    lat=lat,
                    lon=lon,
                    hs=_value_at(wave_heights, idx, 0.0),
                    tp=_value_at(wave_periods, idx, 0.0),
                    dp=_value_at(wave_dirs, idx, 0.0),
                    wind_speed=_value_at(wind_speeds, idx, 0.0),
                    wind_dir=_value_at(wind_dirs, idx, 0.0),
                    swell_height=_value_at(swell_heights, idx, 0.0),
                    swell_period=_value_at(swell_periods, idx, 0.0),
                    swell_direction=_value_at(swell_dirs, idx, 0.0),
                )
            )
        if not points:
            raise ProviderError("Open-Meteo returned no data")
        return points


def _value_at(values: list[float], idx: int, default: float) -> float:
    """배열에서 값 추출. Extract value from array."""

    try:
        value = list(values)[idx]
    except (IndexError, TypeError):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = ["OpenMeteoMarineProvider"]
