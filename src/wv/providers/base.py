"""프로바이더 기본 정의. | Define provider base classes."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Iterable, List

from wv.core.models import ForecastPoint


class ProviderError(Exception):
    """프로바이더 오류 기본. | Base provider error."""


class ProviderRateLimitError(ProviderError):
    """요청 한도 초과 오류. | Rate limit exceeded error."""


class ProviderTimeoutError(ProviderError):
    """타임아웃 오류. | Timeout error."""


class MarineProvider(abc.ABC):
    """해양 데이터 프로바이더 인터페이스. | Marine data provider interface."""

    name: str

    @abc.abstractmethod
    def fetch(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """예측 데이터를 가져옴. | Fetch forecast data."""


@dataclass(slots=True)
class ProviderResult:
    """프로바이더 결과와 출처. | Provider result with source."""

    provider: MarineProvider
    points: Iterable[ForecastPoint]
