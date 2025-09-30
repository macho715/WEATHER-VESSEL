"""Open-Meteo 폴백 커넥터. Open-Meteo fallback connector."""

from __future__ import annotations

import datetime as dt
import logging
from typing import TYPE_CHECKING, Any, Sequence, cast

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

if TYPE_CHECKING:
    from .stormglass import StormglassConnector

OPEN_METEO_URL = "https://marine-api.open-meteo.com/v1/marine"
FALLBACK_STATUS_CODES: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)

logger = logging.getLogger(__name__)


class OpenMeteoFallback:
    """Open-Meteo 예보 폴백. Open-Meteo forecast fallback."""

    def __init__(
        self,
        base_url: str = OPEN_METEO_URL,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url
        self.client = client or httpx.Client(timeout=timeout)

    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        start: dt.datetime,
        end: dt.datetime,
    ) -> MarineTimeseries:
        """Open-Meteo 해양 예보 조회. Fetch Open-Meteo marine forecast."""

        params: dict[str, str | float] = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "significant_wave_height,wave_direction,wave_period,wind_speed_10m,wind_direction_10m,visibility",  # noqa: E501
            "start_date": start.date().isoformat(),
            "end_date": end.date().isoformat(),
            "timezone": "UTC",
        }
        response = self.client.get(self.base_url, params=params)
        response.raise_for_status()
        payload = response.json()
        hourly = payload.get("hourly", {})
        timestamps = hourly.get("time", [])
        points: list[MarineDataPoint] = []
        metadata_units = {
            MarineVariable.SIGNIFICANT_WAVE_HEIGHT: UnitEnum.METERS,
            MarineVariable.WIND_SPEED_10M: UnitEnum.METERS_PER_SECOND,
            MarineVariable.WIND_DIRECTION_10M: UnitEnum.DEGREES,
            MarineVariable.VISIBILITY: UnitEnum.KILOMETERS,
            MarineVariable.SWELL_DIRECTION: UnitEnum.DEGREES,
            MarineVariable.SWELL_PERIOD: UnitEnum.SECONDS,
        }
        for index, timestamp_str in enumerate(timestamps):
            timestamp = dt.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
            else:
                timestamp = timestamp.astimezone(dt.timezone.utc)
            measurements: list[MarineMeasurement] = []
            self._append_measurement(
                hourly,
                "significant_wave_height",
                index,
                MarineVariable.SIGNIFICANT_WAVE_HEIGHT,
                UnitEnum.METERS,
                measurements,
            )
            self._append_measurement(
                hourly,
                "wave_direction",
                index,
                MarineVariable.SWELL_DIRECTION,
                UnitEnum.DEGREES,
                measurements,
            )
            self._append_measurement(
                hourly,
                "wave_period",
                index,
                MarineVariable.SWELL_PERIOD,
                UnitEnum.SECONDS,
                measurements,
            )
            self._append_measurement(
                hourly,
                "wind_speed_10m",
                index,
                MarineVariable.WIND_SPEED_10M,
                UnitEnum.METERS_PER_SECOND,
                measurements,
            )
            self._append_measurement(
                hourly,
                "wind_direction_10m",
                index,
                MarineVariable.WIND_DIRECTION_10M,
                UnitEnum.DEGREES,
                measurements,
            )
            self._append_measurement(
                hourly,
                "visibility",
                index,
                MarineVariable.VISIBILITY,
                UnitEnum.KILOMETERS,
                measurements,
            )
            if not measurements:
                continue
            metadata = TimeseriesMetadata(
                source="open-meteo",
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
    def _append_measurement(
        hourly: dict[str, Any],
        key: str,
        index: int,
        variable: MarineVariable,
        unit: UnitEnum,
        container: list[MarineMeasurement],
    ) -> None:
        values = hourly.get(key)
        if not values:
            return
        try:
            value = values[index]
        except IndexError:
            return
        if value is None:
            return
        container.append(MarineMeasurement(variable=variable, value=float(value), unit=unit))


def fetch_forecast_with_fallback(
    latitude: float,
    longitude: float,
    start: dt.datetime,
    end: dt.datetime,
    primary: "StormglassConnector",
    fallback: "OpenMeteoFallback",
    retry_statuses: Sequence[int] = FALLBACK_STATUS_CODES,
) -> MarineTimeseries:
    """Stormglass 장애 시 폴백. Use Open-Meteo when Stormglass fails."""

    try:
        return primary.fetch_forecast(latitude, longitude, start, end)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status not in retry_statuses:
            raise
        logger.warning("Stormglass HTTP %s triggered fallback: %s", status, exc.response.text)
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        logger.warning("Stormglass request error triggered fallback: %s", exc)
    return fallback.fetch_forecast(latitude, longitude, start, end)
