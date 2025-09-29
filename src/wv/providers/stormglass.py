"""스톰글래스 공급자. Stormglass provider."""

from __future__ import annotations

import datetime as dt
import os
from typing import Any, Iterable, Mapping

from wv.core.models import ForecastPoint
from wv.providers.base import BaseProvider, ProviderError
from wv.utils.http import request_json


class StormglassProvider(BaseProvider):
    """스톰글래스 해양 기상. Stormglass marine weather."""

    def __init__(self) -> None:
        self._endpoint = os.getenv(
            "WV_STORMGLASS_ENDPOINT", "https://api.stormglass.io/v2/weather/point"
        )
        self._api_key = os.getenv("WV_STORMGLASS_API_KEY")

    @property
    def name(self) -> str:
        """공급자 이름. Provider name."""

        return "stormglass"

    def fetch_forecast(self, lat: float, lon: float, hours: int) -> Iterable[ForecastPoint]:
        """예보 조회 수행. Retrieve forecast payload."""

        if not self._api_key:
            raise ProviderError("Stormglass API key missing")
        param_list = [
            "waveHeight",
            "wavePeriod",
            "waveDirection",
            "windSpeed",
            "windDirection",
            "swellHeight",
            "swellPeriod",
            "swellDirection",
        ]
        params = {
            "lat": lat,
            "lng": lon,
            "params": ",".join(param_list),
            "source": "noaa",
            "end": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=hours)).isoformat(),
        }
        headers = {"Authorization": self._api_key}
        payload = request_json(
            "GET",
            self._endpoint,
            params=params,
            headers=headers,
            timeout=self.timeout,
            retries=self.max_retries,
            backoff_factor=self.backoff_factor,
        )
        hours_data = payload.get("hours")
        if not hours_data:
            raise ProviderError("Stormglass payload missing hours")
        points: list[ForecastPoint] = []
        for entry in hours_data:
            points.append(_parse_hour(entry, lat, lon))
        return points


def _parse_hour(entry: Mapping[str, Any], lat: float, lon: float) -> ForecastPoint:
    """스톰글래스 시각 파싱. Parse Stormglass hour."""

    time_raw = entry.get("time")
    if not isinstance(time_raw, str):
        raise ProviderError("Missing time in Stormglass entry")
    time = dt.datetime.fromisoformat(time_raw.replace("Z", "+00:00"))

    def pick(key: str, fallback: float) -> float:
        value = entry.get(key)
        if isinstance(value, Mapping):
            value = value.get("sg", fallback)
        if value is None:
            return fallback
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    return ForecastPoint(
        time=time,
        lat=lat,
        lon=lon,
        hs=pick("waveHeight", 0.0),
        tp=pick("wavePeriod", 0.0),
        dp=pick("waveDirection", 0.0),
        wind_speed=pick("windSpeed", 0.0),
        wind_dir=pick("windDirection", 0.0),
        swell_height=pick("swellHeight", 0.0),
        swell_period=pick("swellPeriod", 0.0),
        swell_direction=pick("swellDirection", 0.0),
    )


__all__ = ["StormglassProvider"]
