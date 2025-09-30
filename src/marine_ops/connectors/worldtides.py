"""WorldTides 커넥터. WorldTides connector."""

from __future__ import annotations

import datetime as dt
from typing import Any, cast

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

WORLDTIDES_URL = "https://www.worldtides.info/api"


class WorldTidesConnector:
    """WorldTides 수위 시계열 수집기. WorldTides tide timeseries fetcher."""

    def __init__(
        self,
        api_key: str,
        client: httpx.Client | None = None,
        base_url: str = WORLDTIDES_URL,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.client = client or httpx.Client(timeout=timeout)

    def fetch_heights(
        self,
        latitude: float,
        longitude: float,
        start: dt.datetime,
        hours: int = 72,
    ) -> MarineTimeseries:
        """WorldTides 수위 30분 시계열 조회. Fetch 30-minute tide heights."""

        params: dict[str, str | int | float] = {
            "heights": "",
            "extremes": "",
            "lat": latitude,
            "lon": longitude,
            "key": self.api_key,
            "step": 30,
            "start": int(start.replace(tzinfo=dt.timezone.utc).timestamp()),
            "length": hours,
        }
        response = self.client.get(self.base_url, params=params)
        response.raise_for_status()
        payload = response.json()
        heights: list[dict[str, Any]] = payload.get("heights", [])
        points: list[MarineDataPoint] = []
        metadata_units = {MarineVariable.TIDE_HEIGHT: UnitEnum.METERS}
        for height in heights:
            timestamp = dt.datetime.fromisoformat(height["date"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
            else:
                timestamp = timestamp.astimezone(dt.timezone.utc)
            value = float(height["height"])
            measurement = MarineMeasurement(
                variable=MarineVariable.TIDE_HEIGHT,
                value=value,
                unit=UnitEnum.METERS,
            )
            metadata = TimeseriesMetadata(
                source="worldtides",
                source_url=cast(HttpUrl, str(httpx.URL(self.base_url))),
                units=metadata_units,
            )
            points.append(
                MarineDataPoint(
                    timestamp=timestamp,
                    position=Position(latitude=latitude, longitude=longitude),
                    measurements=[measurement],
                    metadata=metadata,
                )
            )
        return MarineTimeseries(points=points)
