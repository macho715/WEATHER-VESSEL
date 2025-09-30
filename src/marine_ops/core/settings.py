"""해양 운항 설정. Marine operations settings."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Mapping

import httpx

from wv.core.models import LogiBaseModel

DEFAULT_TIMEOUT = 10.0

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from marine_ops.connectors.open_meteo_fallback import OpenMeteoFallback
    from marine_ops.connectors.stormglass import StormglassConnector
    from marine_ops.connectors.worldtides import WorldTidesConnector


class MarineOpsSettings(LogiBaseModel):
    """환경 변수 기반 설정. Settings derived from environment variables."""

    stormglass_api_key: str | None = None
    worldtides_api_key: str | None = None
    open_meteo_base: str | None = None
    open_meteo_timeout: float = DEFAULT_TIMEOUT
    app_log_level: str = "INFO"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> MarineOpsSettings:
        """환경 변수에서 로드. Load settings from environment."""

        source = os.environ if env is None else env
        timeout_raw = source.get("OPEN_METEO_TIMEOUT")
        timeout = DEFAULT_TIMEOUT
        if timeout_raw:
            try:
                timeout = round(float(timeout_raw), 2)
            except ValueError as exc:  # pragma: no cover - defensive branch
                raise ValueError("OPEN_METEO_TIMEOUT must be numeric") from exc
        return cls(
            stormglass_api_key=source.get("STORMGLASS_API_KEY"),
            worldtides_api_key=source.get("WORLDTIDES_API_KEY"),
            open_meteo_base=source.get("OPEN_METEO_BASE"),
            open_meteo_timeout=timeout,
            app_log_level=source.get("APP_LOG_LEVEL", "INFO"),
        )

    def build_stormglass_connector(self, client: httpx.Client | None = None) -> StormglassConnector:
        """Stormglass 커넥터 생성. Build Stormglass connector."""

        from marine_ops.connectors.stormglass import StormglassConnector

        if not self.stormglass_api_key:
            raise ValueError("STORMGLASS_API_KEY is required for StormglassConnector")
        return StormglassConnector(
            api_key=self.stormglass_api_key,
            client=client or httpx.Client(timeout=self.open_meteo_timeout),
            timeout=self.open_meteo_timeout,
        )

    def build_worldtides_connector(self, client: httpx.Client | None = None) -> WorldTidesConnector:
        """WorldTides 커넥터 생성. Build WorldTides connector."""

        from marine_ops.connectors.worldtides import WorldTidesConnector

        if not self.worldtides_api_key:
            raise ValueError("WORLDTIDES_API_KEY is required for WorldTidesConnector")
        return WorldTidesConnector(
            api_key=self.worldtides_api_key,
            client=client or httpx.Client(timeout=self.open_meteo_timeout),
            timeout=self.open_meteo_timeout,
        )

    def build_open_meteo_fallback(self, client: httpx.Client | None = None) -> OpenMeteoFallback:
        """Open-Meteo 폴백 생성. Build Open-Meteo fallback connector."""

        from marine_ops.connectors.open_meteo_fallback import OPEN_METEO_URL, OpenMeteoFallback

        base_url = self.open_meteo_base or OPEN_METEO_URL
        return OpenMeteoFallback(
            base_url=base_url,
            client=client or httpx.Client(timeout=self.open_meteo_timeout),
            timeout=self.open_meteo_timeout,
        )
