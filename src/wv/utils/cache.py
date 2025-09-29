"""디스크 캐시 도우미. | Disk cache helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Optional

from ..core.models import ForecastPoint


@dataclass(frozen=True)
class CacheKey:
    """캐시 키 표현. | Cache key representation."""

    provider: str
    lat: float
    lon: float
    hours: int

    def digest(self) -> str:
        """고유 해시 생성. | Build unique hash."""

        raw = f"{self.provider}:{self.lat:.4f}:{self.lon:.4f}:{self.hours}"
        return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    """캐시 엔트리 모델. | Cache entry model."""

    points: List[ForecastPoint]
    fresh: bool


class ForecastCache:
    """예보 디스크 캐시. | Forecast disk cache."""

    def __init__(self, root: Path, ttl_seconds: int, stale_ttl_seconds: int) -> None:
        self.root = root
        self.ttl_seconds = ttl_seconds
        self.stale_ttl_seconds = stale_ttl_seconds
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, key: CacheKey) -> Optional[CacheEntry]:
        """캐시 로드. | Load forecast from cache."""

        path = self.root / f"{key.digest()}.json"
        if not path.exists():
            return None
        raw = json.loads(path.read_text("utf-8"))
        timestamp = datetime.fromisoformat(raw["timestamp"])
        age = datetime.now(timezone.utc) - timestamp
        if age > timedelta(seconds=self.stale_ttl_seconds):
            return None
        points = [ForecastPoint.model_validate(item) for item in raw["points"]]
        fresh = age <= timedelta(seconds=self.ttl_seconds)
        return CacheEntry(points=points, fresh=fresh)

    def save(self, key: CacheKey, points: Iterable[ForecastPoint]) -> None:
        """캐시 저장. | Save forecast to cache."""

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "points": [p.model_dump(mode="json") for p in points],
        }
        path = self.root / f"{key.digest()}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
