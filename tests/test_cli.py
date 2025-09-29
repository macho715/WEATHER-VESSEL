from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from wv.cli import app
from wv.core.models import ForecastPoint


class _StubManager:
    def __init__(self, points: list[ForecastPoint]) -> None:
        self.points = points
        self.calls: list[dict[str, Any]] = []

    def fetch_with_fallback(self, *, lat: float, lon: float, hours: int) -> list[ForecastPoint]:
        self.calls.append({"lat": lat, "lon": lon, "hours": hours})
        return self.points


@pytest.fixture(autouse=True)
def patch_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    base_time = datetime(2024, 1, 1, 6, tzinfo=timezone.utc)
    points = [
        ForecastPoint(
            time=base_time + timedelta(hours=idx * 6),
            lat=24.3,
            lon=54.4,
            hs=1.5 + 0.3 * idx,
            tp=8.0,
            dp=120.0,
            wind_speed=15.0 + 2 * idx,
            wind_dir=180.0,
            swell_height=1.2 + 0.2 * idx,
            swell_period=9.0,
            swell_dir=190.0,
        )
        for idx in range(12)
    ]

    monkeypatch.setattr(
        "wv.cli.build_provider_manager",
        lambda: _StubManager(points),
    )


@pytest.fixture()
def runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    monkeypatch.setenv("WV_OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("TZ", "Asia/Dubai")
    return CliRunner()


def test_check_now_outputs_risk_summary(runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--now", "--lat", "24.3", "--lon", "54.4"])
    assert result.exit_code == 0
    assert "Risk Level" in result.stdout
    assert "Hs" in result.stdout


def test_schedule_week_creates_artifacts(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["schedule", "--week", "--route", "MW4-AGI", "--vessel", "DUNE_SAND"],
    )
    assert result.exit_code == 0
    out_dir = tmp_path / "outputs"
    csv_file = out_dir / "schedule_week.csv"
    ics_file = out_dir / "schedule_week.ics"
    assert csv_file.exists()
    assert ics_file.exists()
    assert "Weekly Voyage Schedule" in result.stdout


def test_notify_dry_run_outputs_message(runner: CliRunner) -> None:
    result = runner.invoke(app, ["notify", "--route", "MW4-AGI", "--dry-run"])
    assert result.exit_code == 0
    assert "Route: MW4-AGI" in result.stdout
