"""WV CLI 엔트리포인트. | WV CLI entrypoint."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import typer

from .config import load_config
from .core.models import RiskAssessment, VoyageSlot
from .core.repository import ForecastRepository
from .core.risk import assess_risk
from .core.scheduler import ASIA_DUBAI, suggest_weekly_schedule
from .notify.email import EmailNotifier
from .notify.slack import SlackNotifier
from .notify.telegram import TelegramNotifier
from .providers.copernicus import CopernicusMarineProvider
from .providers.manager import ProviderManager
from .providers.noaa_ww3 import NoaaWaveWatchProvider
from .providers.open_meteo import OpenMeteoMarineProvider
from .providers.stormglass import StormglassProvider
from .utils.logging import configure_logging

app = typer.Typer(help="Weather Vessel control CLI")


def build_provider_manager() -> ProviderManager:
    """프로바이더 관리자 구성. | Build provider manager."""

    config = load_config()
    providers = [
        StormglassProvider(
            api_key=config.provider.stormglass_key, endpoint=config.provider.stormglass_endpoint
        ),
        OpenMeteoMarineProvider(),
        NoaaWaveWatchProvider(),
        CopernicusMarineProvider(
            api_key=config.provider.copernicus_key,
            endpoint=config.provider.copernicus_endpoint,
        ),
    ]
    cache_dir = config.cache_dir
    return ProviderManager(providers=providers, cache_dir=cache_dir)


def build_repository(manager: Optional[ProviderManager] = None) -> ForecastRepository:
    """예보 저장소 생성. | Build forecast repository."""

    return ForecastRepository(manager=manager or build_provider_manager())


def _format_risk(risk: RiskAssessment) -> str:
    """위험 요약 문자열. | Format risk summary string."""

    reasons = "; ".join(risk.reasons[:3])
    return (
        f"Risk Level: {risk.level.value}\n"
        f"Hs Max: {risk.metrics['hs']:.2f} m\n"
        f"Wind Max: {risk.metrics['wind_speed']:.2f} kt\n"
        f"Reasons: {reasons}"
    )


def _render_schedule(slots: Iterable[VoyageSlot]) -> str:
    """스케줄 표 렌더링. | Render schedule table."""

    lines = ["Weekly Voyage Schedule"]
    header = "Day | ETD | ETA | Risk | Notes"
    lines.append(header)
    lines.append("-" * len(header))
    for slot in slots:
        day = slot.etd.strftime("%a %d %b")
        etd = slot.etd.strftime("%Y-%m-%d %H:%M")
        eta = slot.eta.strftime("%Y-%m-%d %H:%M")
        risk = slot.risk.level.value
        notes = "; ".join(slot.notes[:2])
        lines.append(f"{day} | {etd} | {eta} | {risk} | {notes}")
    return "\n".join(lines)


def _write_csv(slots: Iterable[VoyageSlot], path: Path) -> None:
    """CSV 파일 기록. | Write schedule to CSV."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["etd", "eta", "route", "vessel", "risk", "notes"])
        for slot in slots:
            notes = " | ".join(slot.notes)
            writer.writerow(
                [
                    slot.etd.isoformat(),
                    slot.eta.isoformat(),
                    slot.route,
                    slot.vessel,
                    slot.risk.level.value,
                    notes,
                ]
            )


def _write_ics(slots: Iterable[VoyageSlot], path: Path) -> None:
    """ICS 파일 기록. | Write schedule to ICS."""

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WV//Schedule//EN"]
    for slot in slots:
        uid = f"{slot.vessel}-{slot.etd.strftime('%Y%m%d%H%M')}@wv"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.now(tz=ASIA_DUBAI).strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;TZID=Asia/Dubai:{slot.etd.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND;TZID=Asia/Dubai:{slot.eta.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{slot.route} - {slot.vessel}",
                f"DESCRIPTION:{' '.join(slot.notes)}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    path.write_text("\n".join(lines), encoding="utf-8")


def _compose_alert(route: str, risk: RiskAssessment) -> str:
    """알림 메시지 생성. | Compose alert message."""

    return _format_risk(risk) + f"\nRoute: {route}"


@app.callback()
def main_callback() -> None:
    """공통 설정 초기화. | Initialize common settings."""

    configure_logging()


@app.command()
def check(
    now: bool = typer.Option(False, "--now", help="Run immediate risk assessment"),
    lat: Optional[float] = typer.Option(None, help="Latitude"),
    lon: Optional[float] = typer.Option(None, help="Longitude"),
    route: Optional[str] = typer.Option(None, help="Route identifier"),
    hours: int = typer.Option(48, help="Forecast horizon hours"),
) -> None:
    """현재 위험 평가 실행. | Execute current risk assessment."""

    if not now:
        raise typer.BadParameter("Use --now to trigger an immediate check")

    config = load_config()
    repository = build_repository()
    if route:
        route_forecasts = repository.fetch_for_route(route, hours)
        combined = [point for points in route_forecasts.values() for point in points]
    else:
        if lat is None or lon is None:
            raise typer.BadParameter("Latitude and longitude required without route")
        combined = repository.fetch_for_point(lat=lat, lon=lon, hours=hours)

    risk = assess_risk(combined, rules=config.risk_rules)
    typer.echo(_format_risk(risk))


@app.command()
def schedule(
    week: bool = typer.Option(False, "--week", help="Generate 7-day schedule"),
    route: str = typer.Option(..., help="Route identifier"),
    vessel: str = typer.Option(..., help="Vessel name"),
    vessel_speed: Optional[float] = typer.Option(None, help="Vessel speed (kt)"),
    route_distance: Optional[float] = typer.Option(None, help="Route distance (nm)"),
    cargo_hs_limit: Optional[float] = typer.Option(None, help="Cargo wave height limit (m)"),
    hours: int = typer.Option(96, help="Forecast horizon hours"),
) -> None:
    """주간 스케줄 생성. | Generate weekly schedule."""

    if not week:
        raise typer.BadParameter("Use --week to generate weekly schedule")

    config = load_config()
    repository = build_repository()
    forecasts = repository.fetch_for_route(route, hours)
    combined = [point for points in forecasts.values() for point in points]
    slots = suggest_weekly_schedule(
        route=route,
        vessel=vessel,
        points=combined,
        vessel_speed_kt=vessel_speed,
        route_distance_nm=route_distance,
        cargo_hs_limit=cargo_hs_limit,
        rules=config.risk_rules,
    )

    typer.echo(_render_schedule(slots))

    csv_path = config.output_dir / "schedule_week.csv"
    ics_path = config.output_dir / "schedule_week.ics"
    _write_csv(slots, csv_path)
    _write_ics(slots, ics_path)


@app.command()
def notify(
    route: str = typer.Option(..., help="Route identifier"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print message instead of sending"),
    hours: int = typer.Option(48, help="Forecast horizon hours"),
) -> None:
    """스케줄 알림 전송. | Dispatch schedule alerts."""

    config = load_config()
    repository = build_repository()
    forecasts = repository.fetch_for_route(route, hours)
    combined = [point for points in forecasts.values() for point in points]
    risk = assess_risk(combined, rules=config.risk_rules)
    message = _compose_alert(route, risk)

    if dry_run:
        typer.echo(message)
        return

    EmailNotifier(config.notification).send(subject=f"WV Alert {route}", body=message)
    SlackNotifier(config.notification.slack_webhook).send(message)
    TelegramNotifier(config.notification.telegram_token, config.notification.telegram_chat_id).send(
        message
    )
    typer.echo("Notifications dispatched")


if __name__ == "__main__":
    app()
