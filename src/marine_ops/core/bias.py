"""편향 보정 모듈. Bias correction module."""

from __future__ import annotations

from math import isclose
from statistics import mean, pstdev
from typing import Mapping

from .schema import (
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    TimeseriesMetadata,
)


def _stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    mu = mean(values)
    sigma = pstdev(values) if len(values) > 1 else 0.0
    return (mu, sigma)


def apply_bias_correction(
    timeseries: MarineTimeseries,
    background: Mapping[MarineVariable, list[float]],
    enabled: bool = True,
) -> MarineTimeseries:
    """μ/σ 기반 편향 보정. Mean/std based bias correction."""

    if not enabled:
        return timeseries

    value_map: dict[MarineVariable, list[float]] = {}
    for point in timeseries.points:
        for measurement in point.measurements:
            value_map.setdefault(measurement.variable, []).append(measurement.value)

    series_stats: dict[MarineVariable, tuple[float, float]] = {}
    background_stats: dict[MarineVariable, tuple[float, float]] = {}

    for variable, values in value_map.items():
        series_stats[variable] = _stats(values)
        background_values = background.get(variable, [])
        background_stats[variable] = _stats(list(background_values))

    corrected_points: list[MarineDataPoint] = []
    for point in timeseries.points:
        new_measurements: list[MarineMeasurement] = []
        for measurement in point.measurements:
            mu_hat, sigma_hat = series_stats.get(measurement.variable, (0.0, 0.0))
            mu_bg, sigma_bg = background_stats.get(measurement.variable, (0.0, 0.0))
            value = measurement.value
            if isclose(sigma_hat, 0.0) or isclose(sigma_bg, 0.0):
                corrected = value
            else:
                normalized = (value - mu_hat) / sigma_hat
                corrected = normalized * sigma_bg + mu_bg
            new_measurements.append(
                MarineMeasurement(
                    variable=measurement.variable,
                    value=corrected,
                    unit=measurement.unit,
                    quality_flag=measurement.quality_flag,
                )
            )
        metadata = point.metadata
        corrected_metadata = TimeseriesMetadata(
            source=metadata.source,
            source_url=metadata.source_url,
            units=metadata.units,
            bias_corrected=True,
            ensemble_weight=metadata.ensemble_weight,
        )
        corrected_points.append(
            MarineDataPoint(
                timestamp=point.timestamp,
                position=point.position,
                measurements=new_measurements,
                metadata=corrected_metadata,
            )
        )
    return MarineTimeseries(points=corrected_points)
