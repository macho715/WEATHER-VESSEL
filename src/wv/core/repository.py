"""예보 저장소 유틸리티. | Forecast repository utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..providers.manager import ProviderManager
from .models import ForecastPoint

ROUTE_REGISTRY: Dict[str, List[Tuple[float, float]]] = {
    "MW4-AGI": [(24.3488, 54.4651), (24.40, 54.70), (24.45, 54.65)],
    "MW4": [(24.3488, 54.4651)],
    "AGI": [(24.40, 54.70), (24.45, 54.65)],
}


@dataclass(frozen=True)
class ForecastRepository:
    """예보 데이터 접근 계층. | Forecast data access layer."""

    manager: ProviderManager

    def fetch_for_route(self, route: str, hours: int) -> Dict[str, List[ForecastPoint]]:
        """경로 예보 조회. | Fetch forecast for route waypoints."""

        points = ROUTE_REGISTRY.get(route)
        if not points:
            raise ValueError(f"Unknown route {route}")
        result: Dict[str, List[ForecastPoint]] = {}
        for idx, (lat, lon) in enumerate(points):
            key = f"{route}-{idx}"
            result[key] = self.manager.fetch_with_fallback(
                lat=lat,
                lon=lon,
                hours=hours,
            )
        return result

    def fetch_for_point(self, lat: float, lon: float, hours: int) -> List[ForecastPoint]:
        """단일 지점 예보 조회. | Fetch forecast for single point."""

        return self.manager.fetch_with_fallback(lat=lat, lon=lon, hours=hours)
