from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from wv.core.cache import CacheRepository


def test_cache_repository_writes_and_reads(tmp_path: Path) -> None:
    repo = CacheRepository(base_path=tmp_path, ttl=timedelta(hours=3))
    key = repo.make_key("stormglass", {"lat": 24.3, "lon": 54.4})
    payload = {"hs": 1.2}
    repo.store(key, payload)
    cached = repo.load(key)
    assert cached == payload


def test_cache_repository_respects_ttl(tmp_path: Path) -> None:
    repo = CacheRepository(base_path=tmp_path, ttl=timedelta(hours=3))
    key = repo.make_key("stormglass", {"lat": 24.3, "lon": 54.4})
    payload = {"hs": 1.2, "timestamp": datetime.now(timezone.utc).isoformat()}
    repo.store(key, payload, timestamp=datetime.now(timezone.utc) - timedelta(hours=4))
    assert repo.load(key) is None


def test_cache_repository_handles_missing_file(tmp_path: Path) -> None:
    repo = CacheRepository(base_path=tmp_path, ttl=timedelta(hours=3))
    key = repo.make_key("stormglass", {"lat": 24.3, "lon": 54.4})
    assert repo.load(key) is None


@pytest.mark.parametrize("provider", ["stormglass", "open_meteo", "noaa_ww3"])
def test_cache_keys_are_unique_per_provider(tmp_path: Path, provider: str) -> None:
    repo = CacheRepository(base_path=tmp_path, ttl=timedelta(hours=3))
    key_one = repo.make_key(provider, {"lat": 24.3})
    key_two = repo.make_key(provider, {"lat": 24.31})
    assert key_one != key_two
