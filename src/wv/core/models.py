"""도메인 모델 정의. | Define domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogiBaseModel(BaseModel):
    """로지스틱스 기본 모델 기반. | Logistics base model foundation."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class RiskLevel(str, Enum):
    """위험 수준 열거형. | Risk level enumeration."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ForecastPoint(LogiBaseModel):
    """기상 예측 지점을 표현. | Represent a forecast point."""

    time: datetime = Field(..., description="Timestamp of the forecast point")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    hs: Optional[float] = Field(None, description="Significant wave height (m)")
    tp: Optional[float] = Field(None, description="Peak period (s)")
    dp: Optional[float] = Field(None, description="Wave direction (deg)")
    wind_speed: Optional[float] = Field(None, description="Wind speed (kt)")
    wind_dir: Optional[float] = Field(None, description="Wind direction (deg)")
    swell_height: Optional[float] = Field(None, description="Swell height (m)")
    swell_period: Optional[float] = Field(None, description="Swell period (s)")
    swell_direction: Optional[float] = Field(None, description="Swell direction (deg)")


class RiskAssessment(LogiBaseModel):
    """위험 평가 결과를 담음. | Hold risk assessment result."""

    level: RiskLevel
    reasons: List[str]
    metrics: Dict[str, str]
