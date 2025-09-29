import datetime as dt
from pathlib import Path
from typing import Iterable, List

from typer.testing import CliRunner

from wv.cli import app, set_provider_manager_factory
from wv.core.models import ForecastPoint


class _StubManager:
    """더미 공급자 관리자. Stub provider manager."""

    def __init__(self, points: List[ForecastPoint]) -> None:
        self._points = points

    def get_forecast(
        self, lat: float, lon: float, hours: int, use_cache_only: bool = False
    ) -> Iterable[ForecastPoint]:
        return self._points


_runner = CliRunner()


def _forecast_series() -> list[ForecastPoint]:
    base = dt.datetime(2024, 1, 1, 6, tzinfo=dt.timezone.utc)
    points: list[ForecastPoint] = []
    for idx in range(0, 72, 6):
        points.append(
            ForecastPoint(
                time=base + dt.timedelta(hours=idx),
                lat=24.4,
                lon=54.7,
                hs=1.8 + 0.1 * (idx // 6),
                tp=7.5,
                dp=120.0,
                wind_speed=20.0 + idx * 0.2,
                wind_dir=95.0,
                swell_height=1.2,
                swell_period=9.0,
                swell_direction=110.0,
            )
        )
    return points


def test_schedule_week_outputs(tmp_path: Path, monkeypatch) -> None:
    points = _forecast_series()
    set_provider_manager_factory(lambda: _StubManager(points))
    monkeypatch.setenv("WV_OUTPUT_DIR", str(tmp_path))
    result = _runner.invoke(
        app,
        [
            "schedule",
            "--week",
            "--route",
            "MW4-AGI",
            "--vessel",
            "DUNE_SAND",
            "--vessel-speed",
            "12",
            "--route-distance",
            "120",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Schedule for route MW4-AGI" in result.stdout
    csv_path = tmp_path / "schedule_week.csv"
    ics_path = tmp_path / "schedule_week.ics"
    assert csv_path.exists()
    assert ics_path.exists()


def test_check_now(tmp_path: Path, monkeypatch) -> None:
    points = _forecast_series()
    set_provider_manager_factory(lambda: _StubManager(points))
    result = _runner.invoke(
        app,
        [
            "check",
            "--now",
            "--lat",
            "24.40",
            "--lon",
            "54.70",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Risk Level" in result.stdout


def test_notify_dry_run(monkeypatch) -> None:
    points = _forecast_series()
    set_provider_manager_factory(lambda: _StubManager(points))
    result = _runner.invoke(
        app,
        [
            "notify",
            "--route",
            "MW4-AGI",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Dry-run notification" in result.stdout
