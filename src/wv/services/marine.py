"""해양 예측 서비스. | Marine forecast service."""

from __future__ import annotations

import logging
from typing import Any, List, Sequence

from wv.core.cache import CacheRepository
from wv.core.models import ForecastPoint
from wv.providers.base import (
    MarineProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)

LOGGER = logging.getLogger("wv.marine")


class MarineForecastService:
    """프로바이더 순환 예측 서비스. | Forecast service rotating providers."""

    def __init__(
        self,
        providers: Sequence[MarineProvider],
        cache: CacheRepository,
    ) -> None:
        self.providers = list(providers)
        self.cache = cache

    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> List[ForecastPoint]:
        """예측 데이터를 취득. | Acquire forecast data."""
        params = {"lat": lat, "lon": lon, "hours": hours}
        for provider in self.providers:
            key = self.cache.make_key(provider.name, params)
            try:
                points = provider.fetch(lat=lat, lon=lon, hours=hours)
            except ProviderRateLimitError:
                LOGGER.warning("Provider %s rate limited; trying fallback", provider.name)
                continue
            except ProviderTimeoutError:
                LOGGER.warning("Provider %s timed out; trying fallback", provider.name)
                continue
            except ProviderError as exc:
                LOGGER.warning("Provider %s failed: %s", provider.name, exc)
                continue
            if points:
                payload: List[dict[str, Any]] = [point.model_dump(mode="json") for point in points]
                self.cache.store(
                    key,
                    payload=payload,
                )
                return list(points)

        # fallback to cache entries within TTL
        for provider in self.providers:
            key = self.cache.make_key(provider.name, params)
            cached = self.cache.load(key)
            if cached:
                LOGGER.info("Using cached data for provider %s", provider.name)
                return [ForecastPoint.model_validate(item) for item in cached]

        raise ProviderError("No marine forecast data available")
