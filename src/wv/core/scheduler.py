"""일정 생성기. Schedule generator."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from wv.core.models import (
    ForecastPoint,
    NotificationChannel,
    NotificationMessage,
    RiskAssessment,
    RiskLevel,
    RiskReason,
    ScheduleArtifacts,
    ScheduleContext,
    ScheduleSlot,
)
from wv.core.risk import assess_risk
from wv.utils.time import ASIA_DUBAI, ensure_tz, now_dubai, to_utc


def generate_weekly_slots(
    forecast: list[ForecastPoint], context: ScheduleContext
) -> list[ScheduleSlot]:
    """7일 슬롯 생성. Generate 7-day slots."""

    local_now = now_dubai()
    start_date = local_now.date()
    slots: list[ScheduleSlot] = []
    for day_offset in range(7):
        for hour in (6, 17):
            local_start = ensure_tz(
                dt.datetime.combine(start_date + dt.timedelta(days=day_offset), dt.time(hour=hour)),
                ASIA_DUBAI,
            )
            local_end = local_start + dt.timedelta(hours=6)
            slot_points = _select_points(forecast, local_start, local_end)
            if not slot_points:
                slot_points = _nearest_points(forecast, local_start)
            risk = assess_risk(slot_points)
            if (
                context.cargo_hs_limit is not None
                and risk.metrics.max_wave_height > context.cargo_hs_limit
            ):
                risk = _with_cargo_limit(risk, context.cargo_hs_limit)
            etd = local_start
            travel_hours = _travel_hours(context)
            eta = local_start + dt.timedelta(hours=travel_hours) if travel_hours else local_end
            slots.append(
                ScheduleSlot(
                    start=to_utc(local_start),
                    end=to_utc(local_end),
                    etd=to_utc(etd),
                    eta=to_utc(eta),
                    risk=risk,
                )
            )
    return slots


def _travel_hours(context: ScheduleContext) -> float | None:
    """운항 시간 계산. Compute voyage hours."""

    if context.vessel_speed_knots and context.route_distance_nm:
        return context.route_distance_nm / max(context.vessel_speed_knots, 0.1)
    return None


def _select_points(
    forecast: list[ForecastPoint], local_start: dt.datetime, local_end: dt.datetime
) -> list[ForecastPoint]:
    """윈도우 포인트 선택. Select points in window."""

    start_utc = to_utc(local_start)
    end_utc = to_utc(local_end)
    return [point for point in forecast if start_utc <= point.time <= end_utc]


def _nearest_points(forecast: list[ForecastPoint], local_start: dt.datetime) -> list[ForecastPoint]:
    """가장 가까운 포인트 선택. Select nearest points."""

    start_utc = to_utc(local_start)
    nearest = min(forecast, key=lambda point: abs(point.time - start_utc))
    return [nearest]


def _with_cargo_limit(risk: RiskAssessment, limit: float) -> RiskAssessment:
    """화물 제한 반영. Apply cargo limit."""

    reasons = list(risk.reasons)
    reasons.append(
        RiskReason(
            reason_kr=f"화물 Hs 한계 {limit:.2f} m 초과",
            reason_en=f"Cargo Hs limit {limit:.2f} m exceeded",
        )
    )
    level = RiskLevel.HIGH if risk.level is RiskLevel.MEDIUM else risk.level
    if risk.metrics.max_wave_height > limit:
        level = RiskLevel.HIGH
    return RiskAssessment(level=level, reasons=reasons, metrics=risk.metrics)


def export_schedule(slots: list[ScheduleSlot], output_dir: Path) -> ScheduleArtifacts:
    """일정 파일 출력. Export schedule files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "schedule_week.csv"
    ics_path = output_dir / "schedule_week.ics"
    _write_csv(slots, csv_path)
    _write_ics(slots, ics_path)
    return ScheduleArtifacts(csv_path=csv_path, ics_path=ics_path)


def _write_csv(slots: list[ScheduleSlot], path: Path) -> None:
    """CSV 저장. Write CSV file."""

    headers = [
        "start_utc",
        "end_utc",
        "risk_level",
        "max_hs_m",
        "max_wind_kt",
        "dominant_wave_dir_deg",
        "dominant_wind_dir_deg",
        "avg_swell_period_s",
        "reasons_en",
    ]
    with path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for slot in slots:
            writer.writerow(
                [
                    slot.start.isoformat(),
                    slot.end.isoformat(),
                    slot.risk.level.value,
                    f"{slot.risk.metrics.max_wave_height:.2f}",
                    f"{slot.risk.metrics.max_wind_speed:.2f}",
                    _format_optional(slot.risk.metrics.dominant_wave_dir),
                    _format_optional(slot.risk.metrics.dominant_wind_dir),
                    _format_optional(slot.risk.metrics.average_swell_period),
                    " | ".join(reason.reason_en for reason in slot.risk.reasons),
                ]
            )


def _write_ics(slots: list[ScheduleSlot], path: Path) -> None:
    """ICS 저장. Write ICS file."""

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Weather Vessel//EN",
    ]
    for slot in slots:
        uid = uuid5(NAMESPACE_URL, f"wv-{slot.start.isoformat()}")
        summary = f"{slot.risk.level.value} risk window"
        description = "\\n".join(reason.reason_en for reason in slot.risk.reasons)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{slot.start.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{slot.start.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{slot.end.strftime('%Y%m%dT%H%M%SZ')}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    path.write_text("\n".join(lines), encoding="utf-8")


def _format_optional(value: float | None) -> str:
    """옵션 값 포맷. Format optional value."""

    if value is None:
        return ""
    return f"{value:.2f}"


def render_table(slots: list[ScheduleSlot], context: ScheduleContext) -> str:
    """콘솔 테이블 렌더. Render console table."""

    lines = [
        f"Schedule for route {context.route.name} (Asia/Dubai)",
        "Date       | Window  | Risk | Hs(m) | Wind(kt) | Reasons",
        "-----------+---------+------+-------+----------+--------",
    ]
    for slot in slots:
        local_start = slot.start.astimezone(ASIA_DUBAI)
        window = (
            f"{local_start.strftime('%H:%M')}"
            + "-"
            + slot.end.astimezone(ASIA_DUBAI).strftime("%H:%M")
        )
        reasons = "; ".join(reason.reason_en for reason in slot.risk.reasons)
        lines.append(
            "{date} | {window:<7} | {risk:<4} | {hs:>5} | {wind:>8} | {reasons}".format(
                date=local_start.strftime("%Y-%m-%d"),
                window=window,
                risk=slot.risk.level.value[:4].upper(),
                hs=f"{slot.risk.metrics.max_wave_height:.2f}",
                wind=f"{slot.risk.metrics.max_wind_speed:.2f}",
                reasons=reasons,
            )
        )
    return "\n".join(lines)


def build_notification_body(
    slots: list[ScheduleSlot], context: ScheduleContext
) -> NotificationMessage:
    """알림 메시지 구성. Build notification message."""

    top_slot = max(slots, key=lambda slot: slot.risk.metrics.max_wave_height)
    local_window = top_slot.start.astimezone(ASIA_DUBAI).strftime("%Y-%m-%d %H:%M")
    body_lines = [
        f"Route: {context.route.name}",
        f"Highest wave window: {local_window} Asia/Dubai",
        f"Risk Level: {top_slot.risk.level.value}",
        (
            "Hs: "
            f"{top_slot.risk.metrics.max_wave_height:.2f} m, "
            f"Wind: {top_slot.risk.metrics.max_wind_speed:.2f} kt"
        ),
        "Reasons:",
    ]
    body_lines.extend(f"- {reason.reason_en}" for reason in top_slot.risk.reasons)
    body = "\n".join(body_lines)
    subject = f"Weather Vessel Alert - {context.route.name}"
    return NotificationMessage(subject=subject, body=body, channel=contextual_channel())


def contextual_channel() -> NotificationChannel:
    """기본 채널 반환. Return default channel name."""

    return NotificationChannel.EMAIL


__all__ = [
    "generate_weekly_slots",
    "export_schedule",
    "render_table",
    "build_notification_body",
]
