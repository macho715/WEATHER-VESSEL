"""해상 물류 도메인 모델 정의. | Marine logistics domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogiBaseModel(BaseModel):
    """도메인 공통 Pydantic 모델 기반. | Shared domain Pydantic base."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RiskLevel(str, Enum):
    """위험 등급 정의. | Risk level definition."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ForecastPoint(LogiBaseModel):
    """예보 지점 데이터. | Forecast point data."""

    time: datetime
    lat: float
    lon: float
    hs: Optional[float] = Field(default=None, description="Significant wave height in meters")
    tp: Optional[float] = Field(default=None, description="Peak wave period in seconds")
    dp: Optional[float] = Field(default=None, description="Peak wave direction in degrees")
    wind_speed: Optional[float] = Field(default=None, description="Wind speed in knots")
    wind_dir: Optional[float] = Field(default=None, description="Wind direction in degrees")
    swell_height: Optional[float] = Field(default=None, description="Swell height in meters")
    swell_period: Optional[float] = Field(default=None, description="Swell period in seconds")
    swell_dir: Optional[float] = Field(default=None, description="Swell direction in degrees")


class RiskAssessment(LogiBaseModel):
    """위험 평가 결과. | Risk assessment outcome."""

    level: RiskLevel
    reasons: List[str]
    metrics: Dict[str, float]


class VoyageSlot(LogiBaseModel):
    """주간 항차 슬롯. | Weekly voyage slot."""

    etd: datetime
    eta: datetime
    route: str
    vessel: str
    risk: RiskAssessment
    notes: List[str]
