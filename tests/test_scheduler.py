import datetime as dt
from pathlib import Path

from wv.core.models import ForecastPoint, Route, ScheduleContext
from wv.core.scheduler import (
    build_notification_body,
    export_schedule,
    generate_weekly_slots,
    render_table,
)


def _forecast_series() -> list[ForecastPoint]:
    base = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
    points: list[ForecastPoint] = []
    for idx in range(0, 48, 6):
        points.append(
            ForecastPoint(
                time=base + dt.timedelta(hours=idx),
                lat=24.4,
                lon=54.7,
                hs=1.0 + 0.5 * (idx // 6),
                tp=8.0,
                dp=100.0,
                wind_speed=15.0 + idx,
                wind_dir=80.0,
                swell_height=0.8,
                swell_period=8.0,
                swell_direction=90.0,
            )
        )
    return points


def test_generate_slots_and_exports(tmp_path: Path) -> None:
    route = Route(name="MW4-AGI", points=[(24.4, 54.7)])
    context = ScheduleContext(
        route=route,
        vessel_name="TEST",
        vessel_speed_knots=12.0,
        route_distance_nm=120.0,
        cargo_hs_limit=1.2,
    )
    points = _forecast_series()
    slots = generate_weekly_slots(points, context)
    assert len(slots) == 14
    artifacts = export_schedule(slots, tmp_path)
    assert artifacts.csv_path.exists()
    assert artifacts.ics_path.exists()
    table = render_table(slots, context)
    assert "Schedule for route MW4-AGI" in table
    message = build_notification_body(slots, context)
    assert "Weather Vessel Alert" in message.subject
    assert "Hs" in message.body
