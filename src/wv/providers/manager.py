"""프로바이더 관리. Provider management."""

from __future__ import annotations

import logging
from typing import Sequence

from wv.core.models import ForecastPoint, ForecastSeries
from wv.providers.base import BaseProvider, ProviderError
from wv.utils.cache import DiskCache, materialize

LOGGER = logging.getLogger(__name__)


class ProviderManager:
    """공급자 순차 조회기. Sequential provider manager."""

    def __init__(self, providers: Sequence[BaseProvider], cache: DiskCache | None = None) -> None:
        if not providers:
            raise ValueError("At least one provider is required")
        self._providers = providers
        self._cache = cache or DiskCache()

    def get_forecast(
        self,
        lat: float,
        lon: float,
        hours: int,
        *,
        use_cache_only: bool = False,
    ) -> ForecastSeries:
        """예보 데이터 획득. Retrieve forecast data."""

        cache_candidates: list[list[ForecastPoint]] = []
        for provider in self._providers:
            key = self._cache.key(provider.name, round(lat, 3), round(lon, 3), hours)
            LOGGER.debug("Evaluating provider %s for key %s", provider.name, key)
            cached = self._cache.read(key)
            if cached:
                cache_candidates.append(cached)
                if use_cache_only:
                    LOGGER.info("Returning cached forecast for %s from %s", key, provider.name)
                    return cached
            if use_cache_only:
                continue
            try:
                points = materialize(provider(lat, lon, hours))
            except ProviderError as exc:
                LOGGER.warning("Provider %s failed: %s", provider.name, exc)
                continue
            if not points:
                LOGGER.warning("Provider %s returned empty payload", provider.name)
                continue
            self._cache.write(key, points)
            LOGGER.info("Provider %s success with %d points", provider.name, len(points))
            return points

        if cache_candidates:
            LOGGER.info("Falling back to last good cached forecast")
            return cache_candidates[0]

        raise ProviderError("No provider data available and cache empty")


__all__ = ["ProviderManager"]
