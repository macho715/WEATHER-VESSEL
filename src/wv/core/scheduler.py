"""항차 스케줄러 로직. | Voyage scheduler logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional
from zoneinfo import ZoneInfo

from .models import ForecastPoint, RiskAssessment, VoyageSlot
from .risk import RiskRules, assess_risk

ASIA_DUBAI = ZoneInfo("Asia/Dubai")


def suggest_weekly_schedule(
    *,
    route: str,
    vessel: str,
    points: Iterable[ForecastPoint],
    now: Optional[datetime] = None,
    vessel_speed_kt: Optional[float] = None,
    route_distance_nm: Optional[float] = None,
    cargo_hs_limit: Optional[float] = None,
    rules: Optional[RiskRules] = None,
) -> List[VoyageSlot]:
    """7일 스케줄 제안 생성. | Produce rolling seven-day schedule suggestion."""

    current = (now or datetime.now(tz=ASIA_DUBAI)).astimezone(ASIA_DUBAI)
    sorted_points = sorted(points, key=lambda p: p.time)
    rules = rules or RiskRules()
    slots: List[VoyageSlot] = []

    for day in range(7):
        window_start = current.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(
            days=day
        )
        window_end = window_start + timedelta(days=1)
        slice_points = [
            p for p in sorted_points if window_start <= p.time.astimezone(ASIA_DUBAI) < window_end
        ]
        risk: RiskAssessment = assess_risk(slice_points or sorted_points, rules=rules)

        etd = window_start
        duration_hours = _estimate_duration_hours(vessel_speed_kt, route_distance_nm)
        eta = etd + timedelta(hours=duration_hours)

        notes = _build_notes(risk, cargo_hs_limit)

        slots.append(
            VoyageSlot(
                etd=etd,
                eta=eta,
                route=route,
                vessel=vessel,
                risk=risk,
                notes=notes,
            )
        )

    return slots


def _estimate_duration_hours(
    vessel_speed_kt: Optional[float], route_distance_nm: Optional[float]
) -> float:
    """ETA 계산 시간 추정. | Estimate voyage duration hours."""

    if vessel_speed_kt and vessel_speed_kt > 0 and route_distance_nm and route_distance_nm > 0:
        return max(route_distance_nm / vessel_speed_kt, 6.0)
    return 24.0


def _build_notes(risk: RiskAssessment, cargo_hs_limit: Optional[float]) -> List[str]:
    """스케줄 노트 생성. | Build schedule notes."""

    notes = [f"Risk Level: {risk.level.value}"]
    notes.append(
        f"Hs max: {risk.metrics['hs']:.2f} m · Wind max: {risk.metrics['wind_speed']:.2f} kt"
    )
    if cargo_hs_limit is not None and risk.metrics["hs"] > cargo_hs_limit:
        notes.append(f"Cargo limit {cargo_hs_limit:.2f} m exceeded")
    if not risk.reasons:
        return notes
    top_reasons = risk.reasons[:2]
    notes.extend(top_reasons)
    return notes
