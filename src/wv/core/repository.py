"""도메인 저장소. Domain repositories."""

from __future__ import annotations

from typing import Dict, Iterable

from wv.core.models import Route


class RouteRepository:
    """항로 정보 저장소. Route information repository."""

    def __init__(self) -> None:
        self._routes: Dict[str, Route] = {
            "MW4-AGI": Route(
                name="MW4-AGI",
                points=[
                    (24.3488, 54.4651),
                    (24.40, 54.70),
                    (24.45, 54.65),
                ],
            )
        }

    def get(self, name: str) -> Route:
        """항로 조회. Retrieve route."""

        try:
            return self._routes[name.upper()]
        except KeyError as exc:
            raise KeyError(f"Unknown route {name}") from exc

    def list(self) -> Iterable[Route]:
        """등록된 항로 열거. Enumerate registered routes."""

        return self._routes.values()

    def register(self, route: Route) -> None:
        """항로 등록. Register new route."""

        self._routes[route.name.upper()] = route


__all__ = ["RouteRepository"]
