"""위험 평가 로직. Risk assessment logic."""

from __future__ import annotations

import os
from typing import Iterable, Sequence

from wv.core.models import (
    ForecastPoint,
    RiskAssessment,
    RiskConfig,
    RiskLevel,
    RiskMetrics,
    RiskReason,
)


def default_risk_config() -> RiskConfig:
    """환경 기반 기본 위험 설정. Default risk config from env."""

    def _env_float(key: str, default: float) -> float:
        raw = os.getenv(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    return RiskConfig(
        medium_wave_threshold=_env_float("WV_MEDIUM_WAVE_THRESHOLD", 2.0),
        high_wave_threshold=_env_float("WV_HIGH_WAVE_THRESHOLD", 3.0),
        medium_wind_threshold=_env_float("WV_MEDIUM_WIND_THRESHOLD", 22.0),
        high_wind_threshold=_env_float("WV_HIGH_WIND_THRESHOLD", 28.0),
    )


def assess_risk(
    forecast: Sequence[ForecastPoint],
    config: RiskConfig | None = None,
) -> RiskAssessment:
    """예보 기반 위험 평가. Assess risk from forecast."""

    if not forecast:
        raise ValueError("Forecast data required for risk assessment")

    cfg = config or default_risk_config()
    max_wave = max(point.hs for point in forecast)
    max_wind = max(point.wind_speed for point in forecast)
    dominant_wave_dir = _dominant_direction(point.dp for point in forecast)
    dominant_wind_dir = _dominant_direction(point.wind_dir for point in forecast)
    average_swell_period = _mean([point.swell_period for point in forecast if point.swell_period])

    level = RiskLevel.LOW
    reasons: list[RiskReason] = []

    if max_wave >= cfg.high_wave_threshold:
        level = RiskLevel.HIGH
        reasons.append(
            RiskReason(
                reason_kr=(
                    f"유의파고 {max_wave:.2f} m가 고위험 임계값 "
                    f"{cfg.high_wave_threshold:.2f} m 초과"
                ),
                reason_en=(
                    f"Significant wave height {max_wave:.2f} m exceeds "
                    f"high threshold {cfg.high_wave_threshold:.2f} m"
                ),
            )
        )
    elif max_wave >= cfg.medium_wave_threshold:
        level = RiskLevel.MEDIUM
        reasons.append(
            RiskReason(
                reason_kr=(
                    f"유의파고 {max_wave:.2f} m가 중위험 임계값 "
                    f"{cfg.medium_wave_threshold:.2f} m 초과"
                ),
                reason_en=(
                    f"Significant wave height {max_wave:.2f} m exceeds "
                    f"medium threshold {cfg.medium_wave_threshold:.2f} m"
                ),
            )
        )

    if max_wind >= cfg.high_wind_threshold:
        level = RiskLevel.HIGH
        reasons.append(
            RiskReason(
                reason_kr=(
                    f"풍속 {max_wind:.2f} kt가 고위험 임계값 "
                    f"{cfg.high_wind_threshold:.2f} kt 초과"
                ),
                reason_en=(
                    f"Wind speed {max_wind:.2f} kt exceeds high "
                    f"threshold {cfg.high_wind_threshold:.2f} kt"
                ),
            )
        )
    elif max_wind >= cfg.medium_wind_threshold and level is RiskLevel.LOW:
        level = RiskLevel.MEDIUM
        reasons.append(
            RiskReason(
                reason_kr=(
                    f"풍속 {max_wind:.2f} kt가 중위험 임계값 "
                    f"{cfg.medium_wind_threshold:.2f} kt 초과"
                ),
                reason_en=(
                    f"Wind speed {max_wind:.2f} kt exceeds medium "
                    f"threshold {cfg.medium_wind_threshold:.2f} kt"
                ),
            )
        )
    elif max_wind >= cfg.medium_wind_threshold:
        reasons.append(
            RiskReason(
                reason_kr=(
                    f"풍속 {max_wind:.2f} kt가 중위험 임계값 "
                    f"{cfg.medium_wind_threshold:.2f} kt 초과"
                ),
                reason_en=(
                    f"Wind speed {max_wind:.2f} kt exceeds medium "
                    f"threshold {cfg.medium_wind_threshold:.2f} kt"
                ),
            )
        )

    if not reasons:
        reasons.append(
            RiskReason(
                reason_kr="기상 조건이 임계값 아래에 있어 저위험으로 평가",
                reason_en="All monitored conditions are below thresholds; assessed as low risk",
            )
        )

    metrics = RiskMetrics(
        max_wave_height=round(max_wave, 2),
        max_wind_speed=round(max_wind, 2),
        dominant_wave_dir=round(dominant_wave_dir, 2) if dominant_wave_dir is not None else None,
        dominant_wind_dir=round(dominant_wind_dir, 2) if dominant_wind_dir is not None else None,
        average_swell_period=(
            round(average_swell_period, 2) if average_swell_period is not None else None
        ),
    )

    return RiskAssessment(level=level, reasons=reasons, metrics=metrics)


def _dominant_direction(values: Iterable[float]) -> float | None:
    """지배적 방향 계산. Compute dominant direction."""

    values_list = list(values)
    if not values_list:
        return None
    return sum(values_list) / len(values_list)


def _mean(values: Sequence[float]) -> float | None:
    """평균값 계산. Compute arithmetic mean."""

    if not values:
        return None
    return sum(values) / len(values)


__all__ = ["assess_risk", "default_risk_config", "RiskLevel", "RiskAssessment"]
