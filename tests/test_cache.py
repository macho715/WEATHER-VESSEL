import datetime as dt
from pathlib import Path

from wv.core.models import ForecastPoint
from wv.utils.cache import DiskCache, materialize, utcnow


def _point() -> ForecastPoint:
    return ForecastPoint(
        time=dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
        lat=24.4,
        lon=54.7,
        hs=1.0,
        tp=8.0,
        dp=120.0,
        wind_speed=15.0,
        wind_dir=80.0,
        swell_height=0.9,
        swell_period=8.5,
        swell_direction=100.0,
    )


def test_disk_cache_write_read(tmp_path: Path) -> None:
    cache = DiskCache(root=tmp_path, ttl=dt.timedelta(minutes=10))
    key = cache.key("test", 24.4, 54.7, 6)
    cache.write(key, [_point()])
    cached = cache.read(key)
    assert cached is not None
    assert cached[0].hs == 1.0


def test_disk_cache_purge(tmp_path: Path, monkeypatch) -> None:
    cache = DiskCache(root=tmp_path, ttl=dt.timedelta(seconds=0))
    key = cache.key("test", 1, 2, 3)
    cache.write(key, [_point()])
    future = utcnow() + dt.timedelta(hours=1)
    monkeypatch.setattr("wv.utils.cache.utcnow", lambda: future)
    cache.purge()
    assert not list(tmp_path.glob("*.json"))


def test_materialize() -> None:
    assert materialize([_point()])
