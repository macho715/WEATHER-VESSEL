"""ERI 시계열 계산. ERI timeseries computation."""

from __future__ import annotations

import datetime as dt

from wv.core.models import LogiBaseModel

from ..core.schema import MarineDataPoint, MarineMeasurement, MarineTimeseries, MarineVariable
from .rules import ERIRuleSet, ThresholdRule


class QualityBadge(LogiBaseModel):
    """ERI 품질 배지. ERI quality badge."""

    source: str
    has_missing: bool
    bias_corrected: bool


class ERIPoint(LogiBaseModel):
    """ERI 시계열 포인트. ERI timeseries point."""

    timestamp: dt.datetime
    score: float
    quality: QualityBadge


def _score_for_measurement(value: float, rule: ThresholdRule) -> float:
    if rule.direction == "max":
        if value >= rule.danger:
            return 2.0
        if value >= rule.caution:
            return 1.0
        return 0.0
    if value <= rule.danger:
        return 2.0
    if value <= rule.caution:
        return 1.0
    return 0.0


def compute_eri_timeseries(timeseries: MarineTimeseries, rule_set: ERIRuleSet) -> list[ERIPoint]:
    """ERI 규칙 기반 점수 계산. Compute ERI scores from rules."""

    points: list[ERIPoint] = []
    for point in timeseries.points:
        penalty = 0.0
        has_missing = False
        for rule in rule_set.rules:
            measurement = _find_measurement(point, rule.variable)
            if measurement is None:
                has_missing = True
                penalty += rule.weight * rule_set.caution_penalty
                continue
            state = _score_for_measurement(measurement.value, rule)
            if state == 2.0:
                penalty += rule.weight * rule_set.danger_penalty
            elif state == 1.0:
                penalty += rule.weight * rule_set.caution_penalty
        score = max(0.0, rule_set.base_score - penalty)
        points.append(
            ERIPoint(
                timestamp=point.timestamp,
                score=round(score, 2),
                quality=QualityBadge(
                    source=point.metadata.source,
                    has_missing=has_missing,
                    bias_corrected=point.metadata.bias_corrected,
                ),
            )
        )
    return points


def _find_measurement(point: MarineDataPoint, variable: MarineVariable) -> MarineMeasurement | None:
    for measurement in point.measurements:
        if measurement.variable == variable:
            return measurement
    return None
