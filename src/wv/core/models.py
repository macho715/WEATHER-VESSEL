"""도메인 데이터 모델 정의. Domain data models."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

from pydantic import BaseModel, ConfigDict


class LogiBaseModel(BaseModel):
    """물류 표준 베이스 모델. Logistics standard base model."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class ForecastPoint(LogiBaseModel):
    """시간별 예보 지점. Forecast data point."""

    time: dt.datetime
    lat: float
    lon: float
    hs: float
    tp: float
    dp: float
    wind_speed: float
    wind_dir: float
    swell_height: float
    swell_period: float
    swell_direction: float


class RiskLevel(str, Enum):
    """위험 등급. Risk level."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskReason(LogiBaseModel):
    """위험 사유. Risk reason."""

    reason_kr: str
    reason_en: str


class RiskMetrics(LogiBaseModel):
    """핵심 위험 지표. Core risk metrics."""

    max_wave_height: float
    max_wind_speed: float
    dominant_wave_dir: float | None
    dominant_wind_dir: float | None
    average_swell_period: float | None


class RiskAssessment(LogiBaseModel):
    """위험 평가 결과. Risk assessment result."""

    level: RiskLevel
    reasons: Sequence[RiskReason]
    metrics: RiskMetrics


class RiskConfig(LogiBaseModel):
    """위험 임계값 설정. Risk threshold configuration."""

    medium_wave_threshold: float
    high_wave_threshold: float
    medium_wind_threshold: float
    high_wind_threshold: float


class Route(LogiBaseModel):
    """운항 항로 정보. Voyage route metadata."""

    name: str
    points: Sequence[tuple[float, float]]


class ScheduleSlot(LogiBaseModel):
    """항차 일정 슬롯. Voyage schedule slot."""

    start: dt.datetime
    end: dt.datetime
    etd: dt.datetime
    eta: dt.datetime
    risk: RiskAssessment


class ScheduleContext(LogiBaseModel):
    """일정 생성 입력값. Schedule generation context."""

    route: Route
    vessel_name: str | None
    vessel_speed_knots: float | None
    route_distance_nm: float | None
    cargo_hs_limit: float | None


class NotificationChannel(str, Enum):
    """알림 채널 구분. Notification channel type."""

    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"


class NotificationMessage(LogiBaseModel):
    """알림 메시지 구조. Notification message payload."""

    subject: str
    body: str
    channel: NotificationChannel


class ScheduleArtifacts(LogiBaseModel):
    """일정 산출물 경로. Schedule artifact paths."""

    csv_path: Path
    ics_path: Path


ForecastSeries = Iterable[ForecastPoint]
"""예보 시퀀스 타입. Forecast series type."""
