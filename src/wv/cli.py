"""WV CLI 엔트리포인트. WV CLI entrypoint."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, Optional

import typer
from dotenv import load_dotenv

from wv.core.models import ForecastPoint, NotificationChannel, ScheduleContext
from wv.core.repository import RouteRepository
from wv.core.risk import assess_risk
from wv.core.scheduler import (
    build_notification_body,
    export_schedule,
    generate_weekly_slots,
    render_table,
)
from wv.notify.email import send_email
from wv.notify.slack import send_slack
from wv.notify.telegram import send_telegram
from wv.providers.factory import create_manager
from wv.providers.manager import ProviderManager

load_dotenv()

logging.basicConfig(level=os.getenv("WV_LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("wv")

app = typer.Typer(help="Weather Vessel marine scheduling CLI")

ProviderFactory = Callable[[], ProviderManager]
_provider_factory: Optional[ProviderFactory] = None


def get_provider_manager() -> ProviderManager:
    """프로바이더 매니저 획득. Acquire provider manager."""

    factory = _provider_factory or create_manager
    return factory()


def set_provider_manager_factory(factory: ProviderFactory | None) -> None:
    """테스트용 팩토리 설정. Set factory for testing."""

    global _provider_factory
    _provider_factory = factory


_route_repo = RouteRepository()


def _resolve_coordinates(
    route: str | None, lat: float | None, lon: float | None
) -> tuple[float, float, str]:
    """좌표 결정. Resolve coordinates."""

    if route:
        route_obj = _route_repo.get(route)
        point = route_obj.points[0]
        return point[0], point[1], route_obj.name
    if lat is None or lon is None:
        raise typer.BadParameter("Latitude and longitude required when route is not provided")
    return lat, lon, "custom"


def _forecast_points(lat: float, lon: float, hours: int) -> list[ForecastPoint]:
    """예보 포인트 조회. Fetch forecast points."""

    manager = get_provider_manager()
    return list(manager.get_forecast(lat=lat, lon=lon, hours=hours))


def _output_dir() -> Path:
    """출력 디렉토리. Determine output directory."""

    base = Path(os.getenv("WV_OUTPUT_DIR", "outputs"))
    base.mkdir(parents=True, exist_ok=True)
    return base


@app.command()
def check(
    now: bool = typer.Option(False, "--now", help="Fetch immediate forecast"),
    lat: Optional[float] = typer.Option(None, help="Latitude in decimal degrees"),
    lon: Optional[float] = typer.Option(None, help="Longitude in decimal degrees"),
    route: Optional[str] = typer.Option(None, help="Route code, e.g. MW4-AGI"),
    hours: int = typer.Option(48, help="Forecast horizon in hours"),
) -> None:
    """즉시 위험 평가. Immediate risk assessment."""

    lat_val, lon_val, route_name = _resolve_coordinates(route, lat, lon)
    points = _forecast_points(lat_val, lon_val, hours)
    assessment = assess_risk(points)
    typer.echo(f"Risk Level: {assessment.level.value}")
    typer.echo(f"Max Hs: {assessment.metrics.max_wave_height:.2f} m")
    typer.echo(f"Max Wind: {assessment.metrics.max_wind_speed:.2f} kt")
    typer.echo("Reasons:")
    for reason in assessment.reasons:
        typer.echo(f"- {reason.reason_en}")
    if now:
        typer.echo(f"Route: {route_name}")


@app.command()
def schedule(
    week: bool = typer.Option(False, "--week", help="Produce 7-day schedule"),
    route: str = typer.Option("MW4-AGI", help="Route code"),
    vessel: Optional[str] = typer.Option(None, help="Vessel name"),
    vessel_speed: Optional[float] = typer.Option(None, help="Vessel speed in knots"),
    route_distance: Optional[float] = typer.Option(None, help="Route distance in NM"),
    cargo_hs_limit: Optional[float] = typer.Option(None, help="Cargo handling Hs limit in meters"),
) -> None:
    """일정 생성. Generate schedule."""

    if not week:
        raise typer.BadParameter("Only --week schedule is supported")
    route_obj = _route_repo.get(route)
    lat, lon = route_obj.points[0]
    points = _forecast_points(lat, lon, 72)
    context = ScheduleContext(
        route=route_obj,
        vessel_name=vessel,
        vessel_speed_knots=vessel_speed,
        route_distance_nm=route_distance,
        cargo_hs_limit=cargo_hs_limit,
    )
    slots = generate_weekly_slots(points, context)
    artifacts = export_schedule(slots, _output_dir())
    table = render_table(slots, context)
    typer.echo(table)
    typer.echo(f"CSV saved to {artifacts.csv_path}")
    typer.echo(f"ICS saved to {artifacts.ics_path}")


@app.command()
def notify(
    route: str = typer.Option("MW4-AGI", help="Route code"),
    vessel: Optional[str] = typer.Option(None, help="Vessel name"),
    vessel_speed: Optional[float] = typer.Option(None, help="Vessel speed in knots"),
    route_distance: Optional[float] = typer.Option(None, help="Route distance NM"),
    cargo_hs_limit: Optional[float] = typer.Option(None, help="Cargo Hs limit"),
    email_to: list[str] = typer.Option([], "--email-to", help="Email recipients"),
    slack: bool = typer.Option(False, help="Send Slack notification"),
    telegram: bool = typer.Option(False, help="Send Telegram notification"),
    dry_run: bool = typer.Option(False, help="Do not send, just log"),
) -> None:
    """알림 발송. Dispatch notifications."""

    route_obj = _route_repo.get(route)
    lat, lon = route_obj.points[0]
    points = _forecast_points(lat, lon, 72)
    context = ScheduleContext(
        route=route_obj,
        vessel_name=vessel,
        vessel_speed_knots=vessel_speed,
        route_distance_nm=route_distance,
        cargo_hs_limit=cargo_hs_limit,
    )
    slots = generate_weekly_slots(points, context)
    message = build_notification_body(slots, context)

    channels: list[NotificationChannel] = [NotificationChannel.EMAIL]
    if slack:
        channels.append(NotificationChannel.SLACK)
    if telegram:
        channels.append(NotificationChannel.TELEGRAM)

    recipients = email_to or _default_recipients()

    typer.echo("Dry-run notification" if dry_run else "Dispatching notification")
    for channel in channels:
        if channel is NotificationChannel.EMAIL:
            send_email(message, recipients, dry_run=dry_run)
        elif channel is NotificationChannel.SLACK:
            send_slack(message, dry_run=dry_run)
        elif channel is NotificationChannel.TELEGRAM:
            send_telegram(message, dry_run=dry_run)


def _default_recipients() -> list[str]:
    """기본 이메일 대상. Default email recipients."""

    recipients = os.getenv("WV_EMAIL_RECIPIENTS", "")
    return [addr.strip() for addr in recipients.split(",") if addr.strip()]


def main() -> None:
    """엔트리포인트. CLI entrypoint."""

    app()


__all__ = ["app", "main", "set_provider_manager_factory"]
