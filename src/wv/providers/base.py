"""프로바이더 기본 클래스. | Provider base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Mapping

import httpx

from ..core.models import ForecastPoint


@dataclass(frozen=True)
class ProviderError(Exception):
    """프로바이더 오류 표현. | Provider error representation."""

    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class MarineProvider(ABC):
    """해양 기상 프로바이더 추상화. | Marine weather provider abstraction."""

    def __init__(self, name: str, timeout: float = 10.0) -> None:
        self.name = name
        self.timeout = timeout

    @abstractmethod
    def fetch_forecast(self, *, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """예보 조회 인터페이스. | Fetch forecast interface."""

    async def _request_json(
        self,
        url: str,
        params: Mapping[str, str | int | float | bool | None],
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:  # pragma: no cover - network helper
        """HTTP JSON 요청 헬퍼. | HTTP JSON request helper."""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - network errors
                raise ProviderError(
                    "http", f"{self.name} status {exc.response.status_code}"
                ) from exc
            except httpx.TimeoutException as exc:  # pragma: no cover - network errors
                raise ProviderError("timeout", f"{self.name} timeout") from exc
        data = response.json()
        if not isinstance(data, dict):  # pragma: no cover - malformed payload
            raise ProviderError("data", "unexpected response format")
        return data

    @staticmethod
    def _build_point(
        data: Mapping[str, Any], *, time_key: str, lat: float, lon: float
    ) -> ForecastPoint:
        """JSON에서 포인트 생성. | Build forecast point from JSON."""

        timestamp = data.get(time_key)
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        elif isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            raise ProviderError("data", "invalid time field")

        def _opt(name: str) -> float | None:
            value = data.get(name)
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError as exc:  # pragma: no cover - invalid API data
                    raise ProviderError("data", f"invalid numeric field {name}") from exc
            raise ProviderError("data", f"unsupported type for {name}")

        return ForecastPoint(
            time=dt,
            lat=lat,
            lon=lon,
            hs=_opt("hs"),
            tp=_opt("tp"),
            dp=_opt("dp"),
            wind_speed=_opt("wind_speed"),
            wind_dir=_opt("wind_dir"),
            swell_height=_opt("swell_height"),
            swell_period=_opt("swell_period"),
            swell_dir=_opt("swell_dir"),
        )
