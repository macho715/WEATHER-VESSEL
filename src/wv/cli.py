"""WV CLI 엔트리포인트. | WV CLI entrypoint."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from dotenv import load_dotenv

from wv.core.cache import CacheRepository
from wv.core.risk import compute_risk
from wv.core.utils import format_metric
from wv.notify.email import EmailNotifier
from wv.notify.manager import NotificationChannel, NotificationManager
from wv.notify.slack import SlackNotifier
from wv.notify.telegram import TelegramNotifier
from wv.providers.noaa_ww3 import NoaaWaveWatchProvider
from wv.providers.open_meteo import OpenMeteoMarineProvider
from wv.providers.stormglass import StormglassProvider
from wv.services.marine import MarineForecastService
from wv.services.scheduler import VoyageScheduler

app = typer.Typer(help="Marine weather and voyage planning CLI")
LOGGER = logging.getLogger("wv.cli")

ROUTE_COORDS: dict[str, Tuple[float, float]] = {
    "MW4-AGI": (24.3488, 54.4651),
    "AGI-1": (24.40, 54.70),
    "AGI-2": (24.45, 54.65),
}


@dataclass
class ServiceContainer:
    """애플리케이션 서비스 묶음. | Application service bundle."""

    _marine_service: MarineForecastService
    _scheduler: VoyageScheduler
    _notifier: NotificationManager

    def marine_service(self) -> MarineForecastService:
        return self._marine_service

    def scheduler(self) -> VoyageScheduler:
        return self._scheduler

    def notifier(self) -> NotificationManager:
        return self._notifier


def build_service_container() -> ServiceContainer:
    """서비스 컨테이너를 구성. | Build service container."""
    load_dotenv()
    cache = CacheRepository()
    providers = [
        StormglassProvider(),
        OpenMeteoMarineProvider(),
        NoaaWaveWatchProvider(),
    ]
    marine_service = MarineForecastService(providers=providers, cache=cache)
    output_dir = Path(os.getenv("WV_OUTPUT_DIR", "outputs"))
    scheduler = VoyageScheduler(marine_service=marine_service, output_dir=output_dir)
    channels: List[NotificationChannel] = []
    email_channel = EmailNotifier()
    channels.append(email_channel)
    slack_webhook = os.getenv("WV_SLACK_WEBHOOK")
    if slack_webhook:
        channels.append(SlackNotifier(webhook_url=slack_webhook))
    telegram_token = os.getenv("WV_TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("WV_TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat:
        channels.append(TelegramNotifier(bot_token=telegram_token, chat_id=telegram_chat))
    notifier = NotificationManager(channels=channels)
    return ServiceContainer(
        _marine_service=marine_service,
        _scheduler=scheduler,
        _notifier=notifier,
    )


@app.command()
def check(
    now: bool = typer.Option(False, help="Run immediate risk assessment"),
    lat: float = typer.Option(24.3488, help="Latitude"),
    lon: float = typer.Option(54.4651, help="Longitude"),
    hours: int = typer.Option(6, help="Forecast window in hours"),
) -> None:
    """현재 위험을 확인. | Check current risk."""
    if not now:
        typer.echo("Use --now to trigger immediate risk assessment.")
        raise typer.Exit(code=1)
    container = build_service_container()
    service = container.marine_service()
    points = service.get_forecast(lat=lat, lon=lon, hours=hours)
    if not points:
        typer.echo("No forecast data available.")
        raise typer.Exit(code=2)
    point = points[0]
    assessment = compute_risk(point)
    typer.echo(
        "Risk: "
        f"{assessment.level.value} | Hs {format_metric(point.hs, 'm')} | "
        f"Wind {format_metric(point.wind_speed, 'kt')} | Reasons: {', '.join(assessment.reasons)}"
    )


@app.command()
def schedule(
    week: bool = typer.Option(False, help="Generate weekly schedule"),
    lat: float = typer.Option(24.3488, help="Latitude"),
    lon: float = typer.Option(54.4651, help="Longitude"),
    vessel_speed: Optional[float] = typer.Option(None, help="Vessel speed in knots"),
    route_distance_nm: Optional[float] = typer.Option(None, help="Route distance in NM"),
    cargo_hs_limit: Optional[float] = typer.Option(None, help="Cargo handling Hs limit"),
) -> None:
    """주간 일정 생성. | Generate weekly schedule."""
    if not week:
        typer.echo("Use --week to produce weekly schedule.")
        raise typer.Exit(code=1)
    container = build_service_container()
    scheduler_service = container.scheduler()
    table = scheduler_service.generate_weekly_schedule(
        lat=lat,
        lon=lon,
        vessel_speed=vessel_speed,
        route_distance_nm=route_distance_nm,
        cargo_hs_limit=cargo_hs_limit,
    )
    typer.echo(table)


@app.command()
def notify(
    route: str = typer.Option(..., help="Route identifier"),
    dry_run: bool = typer.Option(False, help="Do not send notifications"),
    lat: Optional[float] = typer.Option(None, help="Override latitude"),
    lon: Optional[float] = typer.Option(None, help="Override longitude"),
) -> None:
    """알림을 발송. | Send notifications."""
    container = build_service_container()
    service = container.marine_service()
    notifier = container.notifier()
    coord = ROUTE_COORDS.get(route)
    if coord is None:
        if lat is None or lon is None:
            typer.echo(f"Unknown route {route} and coordinates not provided.")
            raise typer.Exit(code=1)
        target_lat, target_lon = lat, lon
    else:
        target_lat = lat if lat is not None else coord[0]
        target_lon = lon if lon is not None else coord[1]
    points = service.get_forecast(lat=target_lat, lon=target_lon, hours=48)
    if not points:
        typer.echo("No forecast data available.")
        raise typer.Exit(code=2)
    point = points[0]
    assessment = compute_risk(point)
    subject = f"Marine risk update - {route}"
    body = (
        f"Risk Level: {assessment.level.value}\n"
        f"Hs: {format_metric(point.hs, 'm')}\n"
        f"Wind: {format_metric(point.wind_speed, 'kt')}\n"
        f"Reasons: {', '.join(assessment.reasons)}"
    )
    notifier.send_all(subject, body, dry_run=dry_run)
    if dry_run:
        typer.echo("Dry run: notification composed but not sent.")
    else:
        typer.echo("Notifications dispatched.")


def main() -> None:
    """CLI 진입점을 실행. | Run CLI entrypoint."""

    app()


if __name__ == "__main__":  # pragma: no cover
    main()
