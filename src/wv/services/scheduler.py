"""항해 스케줄러 서비스. | Voyage scheduler service."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from wv.core.models import ForecastPoint, RiskLevel
from wv.core.risk import compute_risk
from wv.core.utils import format_metric

RISK_ORDER = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}


@dataclass(slots=True)
class ScheduleEntry:
    """주간 일정 항목. | Weekly schedule entry."""

    date: datetime
    etd: datetime
    eta: datetime
    risk: RiskLevel
    reason: str
    avg_hs: float | None
    avg_wind: float | None


class MarineServiceProtocol(Protocol):
    """해양 서비스 프로토콜. | Protocol for marine service."""

    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> List[ForecastPoint]:
        """예측을 반환. | Return forecast."""


class VoyageScheduler:
    """주간 항해 일정 생성기. | Weekly voyage schedule generator."""

    def __init__(
        self,
        marine_service: MarineServiceProtocol,
        output_dir: Optional[Path] | None = None,
        timezone_name: str = "Asia/Dubai",
    ) -> None:
        self.marine_service = marine_service
        self.tz = ZoneInfo(timezone_name)
        self.output_dir = Path(output_dir or Path("outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_weekly_schedule(
        self,
        lat: float,
        lon: float,
        vessel_speed: float | None = None,
        route_distance_nm: float | None = None,
        cargo_hs_limit: float | None = None,
    ) -> str:
        """7일 항해 일정을 생성. | Generate seven-day voyage schedule."""
        points = self.marine_service.get_forecast(lat=lat, lon=lon, hours=168)
        entries = self._build_entries(points, vessel_speed, route_distance_nm, cargo_hs_limit)
        self._write_csv(entries)
        self._write_ics(entries)
        return self._format_table(entries)

    def _build_entries(
        self,
        points: Iterable[ForecastPoint],
        vessel_speed: float | None,
        route_distance_nm: float | None,
        cargo_hs_limit: float | None,
    ) -> List[ScheduleEntry]:
        points_list = list(points)
        if not points_list:
            return []
        local_now = datetime.now(timezone.utc).astimezone(self.tz)
        earliest_local = min(points_list, key=lambda item: item.time).time.astimezone(self.tz)
        anchor = earliest_local if earliest_local < local_now else local_now
        start_of_day = anchor.replace(hour=0, minute=0, second=0, microsecond=0)
        points_by_day: dict[str, List[ForecastPoint]] = {}
        for point in points_list:
            local_time = point.time.astimezone(self.tz)
            key = local_time.date().isoformat()
            points_by_day.setdefault(key, []).append(point)

        entries: List[ScheduleEntry] = []
        for offset in range(7):
            day_start = start_of_day + timedelta(days=offset)
            day_key = day_start.date().isoformat()
            day_points = points_by_day.get(day_key, [])
            if not day_points:
                continue
            avg_hs = _average([p.hs for p in day_points if p.hs is not None])
            avg_wind = _average([p.wind_speed for p in day_points if p.wind_speed is not None])

            risk, reason = self._daily_risk(day_points, cargo_hs_limit, avg_hs)

            etd = day_start.replace(hour=6)
            eta = etd + self._transit_duration(vessel_speed, route_distance_nm)
            entries.append(
                ScheduleEntry(
                    date=day_start,
                    etd=etd,
                    eta=eta,
                    risk=risk,
                    reason=reason,
                    avg_hs=avg_hs,
                    avg_wind=avg_wind,
                )
            )
        return entries

    def _daily_risk(
        self,
        day_points: List[ForecastPoint],
        cargo_hs_limit: float | None,
        avg_hs: float | None,
    ) -> tuple[RiskLevel, str]:
        highest = RiskLevel.LOW
        chosen_reason = "Conditions within defined safety thresholds"
        for point in day_points:
            assessment = compute_risk(point)
            if RISK_ORDER[assessment.level] > RISK_ORDER[highest]:
                highest = assessment.level
                chosen_reason = "; ".join(assessment.reasons)
        if cargo_hs_limit is not None and avg_hs is not None and avg_hs > cargo_hs_limit:
            highest = RiskLevel.HIGH
            chosen_reason = f"Average Hs {avg_hs:.2f} m exceeds cargo limit {cargo_hs_limit:.2f} m"
        return highest, chosen_reason

    def _transit_duration(
        self,
        vessel_speed: float | None,
        route_distance_nm: float | None,
    ) -> timedelta:
        if vessel_speed and route_distance_nm and vessel_speed > 0:
            hours = route_distance_nm / vessel_speed
            return timedelta(hours=hours)
        return timedelta(hours=12)

    def _write_csv(self, entries: Iterable[ScheduleEntry]) -> None:
        path = self.output_dir / "schedule_week.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Date", "ETD", "ETA", "Hs(m)", "Wind(kt)", "Risk", "Reason"])
            for entry in entries:
                writer.writerow(
                    [
                        entry.date.astimezone(self.tz).strftime("%Y-%m-%d"),
                        entry.etd.astimezone(self.tz).strftime("%Y-%m-%d %H:%M"),
                        entry.eta.astimezone(self.tz).strftime("%Y-%m-%d %H:%M"),
                        format_metric(entry.avg_hs, "m"),
                        format_metric(entry.avg_wind, "kt"),
                        entry.risk.value,
                        entry.reason,
                    ]
                )

    def _write_ics(self, entries: Iterable[ScheduleEntry]) -> None:
        path = self.output_dir / "schedule_week.ics"
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WEATHER-VESSEL//SCHEDULE//EN"]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for entry in entries:
            uid = uuid4().hex
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}@weather-vessel",
                    f"DTSTAMP:{timestamp}",
                    f"DTSTART:{entry.etd.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{entry.eta.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:Voyage slot - {entry.risk.value} risk",
                    f"DESCRIPTION:{entry.reason}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        path.write_text("\n".join(lines), encoding="utf-8")

    def _format_table(self, entries: Iterable[ScheduleEntry]) -> str:
        header = "Weekly Voyage Schedule (Asia/Dubai)\n"
        divider = "=" * 90
        lines = [header, divider]
        lines.append(f"{'Date':<12}{'ETD':<20}{'ETA':<20}{'Hs':<10}{'Wind':<10}{'Risk':<8}Reason")
        for entry in entries:
            lines.append(
                f"{entry.date.astimezone(self.tz).strftime('%Y-%m-%d'):<12}"
                f"{entry.etd.astimezone(self.tz).strftime('%m-%d %H:%M'):<20}"
                f"{entry.eta.astimezone(self.tz).strftime('%m-%d %H:%M'):<20}"
                f"{format_metric(entry.avg_hs, 'm'):<10}"
                f"{format_metric(entry.avg_wind, 'kt'):<10}"
                f"{entry.risk.value:<8}{entry.reason}"
            )
        return "\n".join(lines)


def _average(values: Iterable[float]) -> float | None:
    """평균을 계산. | Compute average."""
    values_list = [value for value in values]
    if not values_list:
        return None
    return sum(values_list) / len(values_list)
