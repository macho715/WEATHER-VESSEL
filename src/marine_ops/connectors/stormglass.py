"""Stormglass 커넥터. Stormglass connector."""

from __future__ import annotations

import datetime as dt
from typing import Any, Sequence, cast

import httpx
from pydantic import HttpUrl

from ..core.schema import (
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    Position,
    TimeseriesMetadata,
    UnitEnum,
)

STORMGLASS_URL = "https://api.stormglass.io/v2/weather/point"
STORMGLASS_PARAMS: tuple[tuple[str, MarineVariable, UnitEnum], ...] = (
    ("waveHeight", MarineVariable.SIGNIFICANT_WAVE_HEIGHT, UnitEnum.METERS),
    ("swellHeight", MarineVariable.SWELL_HEIGHT, UnitEnum.METERS),
    ("swellPeriod", MarineVariable.SWELL_PERIOD, UnitEnum.SECONDS),
    ("swellDirection", MarineVariable.SWELL_DIRECTION, UnitEnum.DEGREES),
    ("windSpeed", MarineVariable.WIND_SPEED_10M, UnitEnum.METERS_PER_SECOND),
    ("windDirection", MarineVariable.WIND_DIRECTION_10M, UnitEnum.DEGREES),
    ("visibility", MarineVariable.VISIBILITY, UnitEnum.KILOMETERS),
)


class StormglassConnector:
    """Stormglass 해양 예보 수집기. Stormglass marine forecast fetcher."""

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        base_url: str = STORMGLASS_URL,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.client = client or httpx.Client(timeout=timeout)

    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        start: dt.datetime,
        end: dt.datetime,
        source_priority: Sequence[str] = ("sg", "noaa"),
    ) -> MarineTimeseries:
        """Stormglass 7-10일 예보 조회. Fetch 7-10 day Stormglass forecast."""

        params: dict[str, str | float] = {
            "lat": latitude,
            "lng": longitude,
            "params": ",".join(key for key, *_ in STORMGLASS_PARAMS),
            "start": start.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "end": end.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": ",".join(source_priority),
        }
        headers = {"Authorization": self.api_key}
        response = self.client.get(self.base_url, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()
        hours: list[dict[str, Any]] = payload.get("hours", [])
        metadata_units = {variable: unit for _, variable, unit in STORMGLASS_PARAMS}
        points: list[MarineDataPoint] = []
        for hour in hours:
            timestamp = dt.datetime.fromisoformat(hour["time"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
            else:
                timestamp = timestamp.astimezone(dt.timezone.utc)
            measurements: list[MarineMeasurement] = []
            for key, variable, unit in STORMGLASS_PARAMS:
                value_entry = hour.get(key)
                if not isinstance(value_entry, dict):
                    continue
                value = self._choose_source(value_entry, source_priority)
                if value is None:
                    continue
                measurements.append(
                    MarineMeasurement(variable=variable, value=float(value), unit=unit)
                )
            if not measurements:
                continue
            metadata = TimeseriesMetadata(
                source="stormglass",
                source_url=cast(HttpUrl, str(httpx.URL(self.base_url))),
                units=metadata_units,
            )
            points.append(
                MarineDataPoint(
                    timestamp=timestamp,
                    position=Position(latitude=latitude, longitude=longitude),
                    measurements=measurements,
                    metadata=metadata,
                )
            )
        return MarineTimeseries(points=points)

    @staticmethod
    def _choose_source(value_entry: dict[str, Any], priority: Sequence[str]) -> float | None:
        for source in priority:
            if source in value_entry and value_entry[source] is not None:
                return float(value_entry[source])
        for value in value_entry.values():
            if value is not None:
                return float(value)
        return None
