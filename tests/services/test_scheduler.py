from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import pytest

from wv.core.models import ForecastPoint
from wv.services.scheduler import VoyageScheduler


class FakeMarineService:
    def __init__(self, points: List[ForecastPoint]) -> None:
        self._points = points

    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> List[ForecastPoint]:
        return self._points


@pytest.fixture
def forecast_points() -> List[ForecastPoint]:
    base = datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc)
    points: List[ForecastPoint] = []
    for day in range(7):
        timestamp = base + timedelta(days=day, hours=6)
        points.append(
            ForecastPoint(
                time=timestamp,
                lat=24.3,
                lon=54.4,
                hs=1.5 + day * 0.2,
                tp=10.0,
                dp=180.0,
                wind_speed=15.0 + day,
                wind_dir=100.0,
                swell_height=1.2 + day * 0.2,
                swell_period=12.0,
                swell_direction=190.0,
            )
        )
    return points


def test_generate_weekly_schedule_outputs_files(
    tmp_path: Path, forecast_points: List[ForecastPoint]
) -> None:
    service = FakeMarineService(forecast_points)
    scheduler = VoyageScheduler(
        marine_service=service,
        output_dir=tmp_path,
    )
    table = scheduler.generate_weekly_schedule(
        lat=24.3,
        lon=54.4,
        vessel_speed=12.0,
        route_distance_nm=120.0,
        cargo_hs_limit=2.5,
    )
    assert "Asia/Dubai" in table
    csv_path = tmp_path / "schedule_week.csv"
    ics_path = tmp_path / "schedule_week.ics"
    assert csv_path.exists()
    assert ics_path.exists()
    csv_content = csv_path.read_text(encoding="utf-8")
    assert "Risk" in csv_content
    ics_content = ics_path.read_text(encoding="utf-8")
    assert "BEGIN:VEVENT" in ics_content


def test_schedule_respects_cargo_limit(
    tmp_path: Path, forecast_points: List[ForecastPoint]
) -> None:
    service = FakeMarineService(forecast_points)
    scheduler = VoyageScheduler(marine_service=service, output_dir=tmp_path)
    table = scheduler.generate_weekly_schedule(
        lat=24.3,
        lon=54.4,
        vessel_speed=12.0,
        route_distance_nm=120.0,
        cargo_hs_limit=1.6,
    )
    assert "High" in table or "Medium" in table
