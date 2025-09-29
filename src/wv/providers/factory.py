"""프로바이더 생성기. Provider factory."""

from __future__ import annotations

from typing import Sequence

from wv.providers.base import BaseProvider
from wv.providers.copernicus import CopernicusMarineProvider
from wv.providers.manager import ProviderManager
from wv.providers.noaa_ww3 import NoaaWaveWatchProvider
from wv.providers.open_meteo import OpenMeteoMarineProvider
from wv.providers.sample import SampleProvider
from wv.providers.stormglass import StormglassProvider
from wv.utils.cache import DiskCache


def create_providers() -> Sequence[BaseProvider]:
    """기본 공급자 목록. Build default provider list."""

    providers: list[BaseProvider] = [
        StormglassProvider(),
        OpenMeteoMarineProvider(),
        NoaaWaveWatchProvider(),
    ]
    try:
        providers.append(CopernicusMarineProvider())
    except Exception:  # noqa: BLE001
        pass
    providers.append(SampleProvider())
    return providers


def create_manager() -> ProviderManager:
    """기본 매니저 생성. Create default manager."""

    cache = DiskCache()
    return ProviderManager(create_providers(), cache)


__all__ = ["create_manager", "create_providers"]
