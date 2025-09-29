"""디스크 캐시 유틸리티. Disk cache utilities."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from wv.core.models import ForecastPoint

DEFAULT_TTL = dt.timedelta(hours=3)


def utcnow() -> dt.datetime:
    """UTC 현재 시각. Current UTC time."""

    return dt.datetime.now(dt.timezone.utc)


class DiskCache:
    """간단한 JSON 디스크 캐시. Simple JSON disk cache."""

    def __init__(self, root: Path | None = None, ttl: dt.timedelta = DEFAULT_TTL) -> None:
        self._root = root or Path.home() / ".wv" / "cache"
        self._root.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl

    def key(self, provider: str, *parts: object) -> str:
        """캐시 키 생성. Build cache key."""

        payload = ":".join(str(part) for part in parts)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{provider}_{digest}"

    def path(self, key: str) -> Path:
        """키 기준 경로. Path for key."""

        return self._root / f"{key}.json"

    def write(self, key: str, points: Sequence[ForecastPoint]) -> None:
        """예보를 저장. Persist forecast."""

        data = {
            "stored_at": utcnow().isoformat(),
            "points": [point.model_dump(mode="json") for point in points],
        }
        self.path(key).write_text(json.dumps(data), encoding="utf-8")

    def read(self, key: str) -> list[ForecastPoint] | None:
        """캐시 로드. Load cache entry."""

        path = self.path(key)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        stored_at = dt.datetime.fromisoformat(raw["stored_at"])
        if stored_at.tzinfo is None:
            stored_at = stored_at.replace(tzinfo=dt.timezone.utc)
        if utcnow() - stored_at > self._ttl:
            return None
        return [ForecastPoint(**point) for point in raw["points"]]

    def purge(self) -> None:
        """TTL 초과 항목 삭제. Remove expired entries."""

        for file in self._root.glob("*.json"):
            try:
                raw = json.loads(file.read_text(encoding="utf-8"))
                stored_at = dt.datetime.fromisoformat(raw.get("stored_at", ""))
                if stored_at.tzinfo is None:
                    stored_at = stored_at.replace(tzinfo=dt.timezone.utc)
            except Exception:  # noqa: BLE001
                file.unlink(missing_ok=True)
                continue
            if utcnow() - stored_at > self._ttl:
                file.unlink(missing_ok=True)


def materialize(points: Iterable[ForecastPoint]) -> list[ForecastPoint]:
    """이터러블을 리스트화. Materialize iterable to list."""

    return list(points)


__all__ = ["DiskCache", "utcnow", "materialize"]
