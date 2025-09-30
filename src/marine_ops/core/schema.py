"""해양 운항 표준 스키마. Marine operations standard schema."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Iterable, Mapping, Sequence

from pydantic import Field, HttpUrl, field_validator, model_validator

from wv.core.models import LogiBaseModel

CSV_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CSV_HEADER: tuple[str, ...] = (
    "timestamp",
    "latitude",
    "longitude",
    "variable",
    "value",
    "unit",
    "source",
    "quality_flag",
    "bias_corrected",
    "ensemble_weight",
)


class MarineVariable(str, Enum):
    """해양 변수 식별자. Marine variable identifier."""

    SIGNIFICANT_WAVE_HEIGHT = "Hs"
    WIND_SPEED_10M = "U10"
    WIND_DIRECTION_10M = "U10_DIR"
    VISIBILITY = "Vis"
    SWELL_HEIGHT = "SwellHs"
    SWELL_PERIOD = "SwellTp"
    SWELL_DIRECTION = "SwellDir"
    TIDE_HEIGHT = "Tide"


class UnitEnum(str, Enum):
    """단위 열거형. Unit enumeration."""

    METERS = "m"
    METERS_PER_SECOND = "m/s"
    DEGREES = "deg"
    KILOMETERS = "km"
    SECONDS = "s"


class QualityFlag(str, Enum):
    """품질 관리 플래그. Quality control flag."""

    RAW = "raw"
    CLIPPED = "clipped"
    IMPUTED = "imputed"


class Position(LogiBaseModel):
    """위치 좌표. Position coordinates."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class MarineMeasurement(LogiBaseModel):
    """해양 변수 관측값. Marine variable measurement."""

    variable: MarineVariable
    value: float
    unit: UnitEnum
    quality_flag: QualityFlag = QualityFlag.RAW

    @model_validator(mode="after")
    def _round_value(self) -> "MarineMeasurement":
        object.__setattr__(self, "value", round(self.value, 2))
        return self


class TimeseriesMetadata(LogiBaseModel):
    """시계열 메타데이터. Timeseries metadata."""

    source: str
    source_url: HttpUrl | None = None
    units: Mapping[MarineVariable, UnitEnum]
    bias_corrected: bool = False
    ensemble_weight: float | None = None

    @model_validator(mode="after")
    def _round_weight(self) -> "TimeseriesMetadata":
        if self.ensemble_weight is not None:
            object.__setattr__(self, "ensemble_weight", round(float(self.ensemble_weight), 2))
        return self


class MarineDataPoint(LogiBaseModel):
    """표준화된 해양 데이터 포인트. Standardized marine data point."""

    timestamp: dt.datetime
    position: Position
    measurements: Sequence[MarineMeasurement]
    metadata: TimeseriesMetadata

    @field_validator("timestamp")
    @classmethod
    def _ensure_utc(cls, value: dt.datetime) -> dt.datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        else:
            value = value.astimezone(dt.timezone.utc)
        return value


class MarineTimeseries(LogiBaseModel):
    """표준 해양 시계열. Standard marine timeseries."""

    points: Sequence[MarineDataPoint]

    def iter_rows(self) -> Iterable[tuple[str, ...]]:
        """RFC 4180 행 이터레이터. RFC 4180 row iterator."""

        for point in self.points:
            iso_time = point.timestamp.strftime(CSV_TIMESTAMP_FORMAT)
            for measurement in point.measurements:
                yield (
                    iso_time,
                    f"{point.position.latitude:.2f}",
                    f"{point.position.longitude:.2f}",
                    measurement.variable.value,
                    f"{measurement.value:.2f}",
                    measurement.unit.value,
                    point.metadata.source,
                    measurement.quality_flag.value,
                    "true" if point.metadata.bias_corrected else "false",
                    (
                        f"{point.metadata.ensemble_weight:.2f}"
                        if point.metadata.ensemble_weight is not None
                        else ""
                    ),
                )
