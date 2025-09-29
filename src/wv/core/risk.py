"""위험 평가 로직. | Risk assessment logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .models import ForecastPoint, RiskAssessment, RiskLevel


@dataclass(frozen=True)
class RiskRules:
    """위험 규칙 한계값. | Risk rule thresholds."""

    medium_hs: float = 2.0
    high_hs: float = 3.0
    medium_wind: float = 22.0
    high_wind: float = 28.0


def assess_risk(points: Iterable[ForecastPoint], rules: RiskRules) -> RiskAssessment:
    """예보 목록 위험 평가. | Assess risk across forecast points."""

    highest_level = RiskLevel.LOW
    reasons: List[str] = []
    metrics = {
        "hs": 0.0,
        "wind_speed": 0.0,
    }

    for point in points:
        if point.hs is not None and point.hs > metrics["hs"]:
            metrics["hs"] = point.hs
        if point.wind_speed is not None and point.wind_speed > metrics["wind_speed"]:
            metrics["wind_speed"] = point.wind_speed

        level = RiskLevel.LOW
        local_reasons: List[str] = []
        if point.hs is not None:
            if point.hs >= rules.high_hs:
                level = RiskLevel.HIGH
                local_reasons.append(f"Hs {point.hs:.2f} m ≥ {rules.high_hs:.2f} m")
            elif point.hs >= rules.medium_hs:
                level = max(level, RiskLevel.MEDIUM, key=_level_weight)
                local_reasons.append(f"Hs {point.hs:.2f} m ≥ {rules.medium_hs:.2f} m")
        if point.wind_speed is not None:
            if point.wind_speed >= rules.high_wind:
                level = RiskLevel.HIGH
                local_reasons.append(f"Wind {point.wind_speed:.2f} kt ≥ {rules.high_wind:.2f} kt")
            elif point.wind_speed >= rules.medium_wind:
                level = max(level, RiskLevel.MEDIUM, key=_level_weight)
                local_reasons.append(f"Wind {point.wind_speed:.2f} kt ≥ {rules.medium_wind:.2f} kt")

        if point.swell_period is None or point.swell_dir is None:
            local_reasons.append("Missing swell data → conservative Medium")
            level = max(level, RiskLevel.MEDIUM, key=_level_weight)

        if _level_weight(level) > _level_weight(highest_level):
            highest_level = level
        reasons.extend(local_reasons)

    if not reasons:
        reasons.append("No significant hazards detected")

    return RiskAssessment(level=highest_level, reasons=reasons, metrics=metrics)


def _level_weight(level: RiskLevel) -> int:
    """위험 등급 가중치. | Convert risk level to weight."""

    return {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}[level]
