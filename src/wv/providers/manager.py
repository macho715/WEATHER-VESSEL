"""프로바이더 관리 로직. | Provider management logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from ..core.models import ForecastPoint
from ..utils.cache import CacheKey, ForecastCache
from .base import MarineProvider, ProviderError

LOGGER = logging.getLogger("wv.providers")


class ProviderManager:
    """프로바이더 폴백 관리자. | Provider fallback manager."""

    def __init__(
        self,
        *,
        providers: Iterable[MarineProvider],
        cache_dir: Path,
        cache_ttl_seconds: int = 1800,
        stale_ttl_seconds: int = 10800,
    ) -> None:
        self.providers = list(providers)
        self.cache = ForecastCache(
            cache_dir, ttl_seconds=cache_ttl_seconds, stale_ttl_seconds=stale_ttl_seconds
        )

    def fetch_with_fallback(self, *, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """폴백 및 캐시 조회. | Fetch with fallback and caching."""

        key = CacheKey(provider="multi", lat=lat, lon=lon, hours=hours)
        cached = self.cache.load(key)
        if cached and cached.fresh:
            LOGGER.info("cache-hit", extra={"lat": lat, "lon": lon, "hours": hours})
            return cached.points

        last_error: ProviderError | None = None
        for provider in self.providers:
            try:
                LOGGER.info(
                    "fetch-attempt", extra={"provider": provider.name, "lat": lat, "lon": lon}
                )
                points = provider.fetch_forecast(lat=lat, lon=lon, hours=hours)
                if not points:
                    raise ProviderError("empty", f"{provider.name} returned no data")
                self.cache.save(key, points)
                return points
            except ProviderError as error:
                LOGGER.warning(
                    "provider-failed",
                    extra={"provider": provider.name, "code": error.code, "detail": error.message},
                )
                last_error = error
                continue

        if cached:
            LOGGER.info("cache-stale-hit", extra={"lat": lat, "lon": lon, "hours": hours})
            return cached.points

        raise ProviderError(last_error.code if last_error else "unknown", "All providers failed")
