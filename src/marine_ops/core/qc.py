"""해양 데이터 품질 관리. Marine data quality control."""

from __future__ import annotations

from collections import defaultdict
from statistics import quantiles
from typing import Mapping, Sequence

from .schema import (
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    QualityFlag,
)


def _clip_value(value: float, minimum: float | None, maximum: float | None) -> float:
    if minimum is not None and value < minimum:
        return minimum
    if maximum is not None and value > maximum:
        return maximum
    return value


def compute_iqr_bounds(values: Sequence[float], multiplier: float) -> tuple[float, float]:
    """IQR 경계 계산. Compute IQR bounds."""

    if len(values) < 4:
        return (float("-inf"), float("inf"))
    q1, q2, q3 = quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return (lower, upper)


def apply_quality_controls(
    timeseries: MarineTimeseries,
    physical_bounds: Mapping[MarineVariable, tuple[float | None, float | None]],
    iqr_multiplier: float = 1.5,
) -> MarineTimeseries:
    """결측/이상치 품질 관리 적용. Apply missing/outlier quality controls."""

    value_collector: dict[MarineVariable, list[float]] = defaultdict(list)
    for point in timeseries.points:
        for measurement in point.measurements:
            value_collector[measurement.variable].append(measurement.value)

    iqr_bounds: dict[MarineVariable, tuple[float, float]] = {}
    for variable, values in value_collector.items():
        lower, upper = compute_iqr_bounds(values, iqr_multiplier)
        iqr_bounds[variable] = (lower, upper)

    cleaned_points: list[MarineDataPoint] = []
    for point in timeseries.points:
        new_measurements: list[MarineMeasurement] = []
        for measurement in point.measurements:
            bounds = physical_bounds.get(measurement.variable, (None, None))
            iqr_bound = iqr_bounds.get(measurement.variable, (float("-inf"), float("inf")))
            min_bound = bounds[0]
            max_bound = bounds[1]
            value = measurement.value
            clipped_value = _clip_value(value, min_bound, max_bound)
            clipped_value = _clip_value(clipped_value, iqr_bound[0], iqr_bound[1])
            flag = measurement.quality_flag
            if round(clipped_value, 2) != round(value, 2):
                flag = QualityFlag.CLIPPED
            new_measurements.append(
                MarineMeasurement(
                    variable=measurement.variable,
                    value=clipped_value,
                    unit=measurement.unit,
                    quality_flag=flag,
                )
            )
        cleaned_points.append(
            MarineDataPoint(
                timestamp=point.timestamp,
                position=point.position,
                measurements=new_measurements,
                metadata=point.metadata,
            )
        )
    return MarineTimeseries(points=cleaned_points)
