from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from typer.testing import CliRunner

from wv.cli import app
from wv.core.models import ForecastPoint


class DummyContainer:
    def __init__(self, points: List[ForecastPoint], output_dir: Path) -> None:
        self.points = points
        self.output_dir = output_dir

    def marine_service(self):
        return self

    def scheduler(self):
        from wv.services.scheduler import VoyageScheduler

        return VoyageScheduler(marine_service=self, output_dir=self.output_dir)

    def notifier(self):
        from wv.notify.manager import NotificationManager

        return NotificationManager(channels=[])

    # Methods consumed by CLI
    def get_forecast(self, lat: float, lon: float, hours: int = 48):
        return self.points

    def send_notifications(self, subject: str, body: str) -> None:
        pass


runner = CliRunner()


def _make_point() -> ForecastPoint:
    return ForecastPoint(
        time=datetime.now(timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=2.2,
        tp=9.0,
        dp=180.0,
        wind_speed=25.0,
        wind_dir=120.0,
        swell_height=2.0,
        swell_period=11.0,
        swell_direction=200.0,
    )


def test_cli_check_now(monkeypatch, tmp_path: Path) -> None:
    container = DummyContainer(points=[_make_point()], output_dir=tmp_path)

    def fake_container() -> DummyContainer:
        return container

    monkeypatch.setattr("wv.cli.build_service_container", fake_container)
    result = runner.invoke(app, ["check", "--now", "--lat", "24.3", "--lon", "54.4"])
    assert result.exit_code == 0
    assert "Risk" in result.stdout


def test_cli_schedule_week_creates_outputs(monkeypatch, tmp_path: Path) -> None:
    container = DummyContainer(points=[_make_point()], output_dir=tmp_path)

    def fake_container() -> DummyContainer:
        return container

    monkeypatch.setattr("wv.cli.build_service_container", fake_container)
    result = runner.invoke(app, ["schedule", "--week", "--lat", "24.3", "--lon", "54.4"])
    assert result.exit_code == 0
    assert (tmp_path / "schedule_week.csv").exists()
    assert (tmp_path / "schedule_week.ics").exists()


def test_cli_notify_dry_run(monkeypatch, tmp_path: Path) -> None:
    container = DummyContainer(points=[_make_point()], output_dir=tmp_path)

    def fake_container() -> DummyContainer:
        return container

    monkeypatch.setattr("wv.cli.build_service_container", fake_container)
    result = runner.invoke(app, ["notify", "--route", "MW4-AGI", "--dry-run"])
    assert result.exit_code == 0
    assert "Dry run" in result.stdout
