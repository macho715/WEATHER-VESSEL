"""디스크 캐시를 관리. | Manage disk cache."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Union

CacheData = Union[Dict[str, Any], List[Any]]


class CacheRepository:
    """해상 데이터 캐시 저장소. | Marine data cache repository."""

    def __init__(self, base_path: Path | None = None, ttl: timedelta | None = None) -> None:
        self.base_path = base_path or Path.home() / ".wv" / "cache"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl or timedelta(hours=3)

    def make_key(self, provider: str, params: Dict[str, Any]) -> str:
        """요청 키를 해시 생성. | Hash request parameters into key."""
        fingerprint = json.dumps(
            {"provider": provider, "params": params}, sort_keys=True, default=str
        )
        digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        return f"{provider}_{digest}"

    def _resolve_path(self, key: str) -> Path:
        """키에 대한 경로 계산. | Resolve filesystem path for key."""
        return self.base_path / f"{key}.json"

    def store(self, key: str, payload: CacheData, timestamp: datetime | None = None) -> None:
        """캐시를 저장. | Store cache payload."""
        envelope = {
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "payload": payload,
        }
        self._resolve_path(key).write_text(
            json.dumps(envelope, ensure_ascii=False), encoding="utf-8"
        )

    def load(self, key: str) -> CacheData | None:
        """캐시를 로드. | Load cache payload."""
        path = self._resolve_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            timestamp = datetime.fromisoformat(data["timestamp"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
        if datetime.now(timezone.utc) - timestamp > self.ttl:
            return None
        payload = data.get("payload")
        if isinstance(payload, (dict, list)):
            return payload
        return None
