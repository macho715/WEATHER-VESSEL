"""가중 앙상블 계산. Weighted ensemble computation."""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence

from .schema import (
    CSV_TIMESTAMP_FORMAT,
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    QualityFlag,
    TimeseriesMetadata,
)


def _normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total == 0:
        raise ValueError("Ensemble weights must have positive sum")
    return {source: round(value / total, 4) for source, value in weights.items()}


def weighted_ensemble(
    series_list: Sequence[MarineTimeseries],
    weights: Mapping[str, float],
) -> MarineTimeseries:
    """가중 앙상블 시계열 계산. Compute weighted ensemble timeseries."""

    normalized = _normalize_weights(weights)
    value_bucket: dict[str, dict[MarineVariable, list[tuple[MarineMeasurement, float]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    position_bucket: dict[str, MarineDataPoint] = {}
    bias_flag: dict[str, bool] = defaultdict(bool)

    for series in series_list:
        for point in series.points:
            source = point.metadata.source
            weight = normalized.get(source)
            if weight is None:
                continue
            key = point.timestamp.strftime(CSV_TIMESTAMP_FORMAT)
            position_bucket.setdefault(key, point)
            bias_flag[key] = bias_flag[key] or point.metadata.bias_corrected
            for measurement in point.measurements:
                value_bucket[key][measurement.variable].append((measurement, weight))

    ensemble_points: list[MarineDataPoint] = []
    for key, variable_map in sorted(value_bucket.items()):
        base_point = position_bucket[key]
        aggregated_measurements: list[MarineMeasurement] = []
        for variable, measurements in variable_map.items():
            weight_sum = sum(weight for _, weight in measurements)
            if weight_sum == 0:
                continue
            value = (
                sum(measurement.value * weight for measurement, weight in measurements) / weight_sum
            )
            flags = {measurement.quality_flag for measurement, _ in measurements}
            if QualityFlag.CLIPPED in flags:
                flag = QualityFlag.CLIPPED
            elif QualityFlag.IMPUTED in flags:
                flag = QualityFlag.IMPUTED
            else:
                flag = QualityFlag.RAW
            aggregated_measurements.append(
                MarineMeasurement(
                    variable=variable,
                    value=value,
                    unit=measurements[0][0].unit,
                    quality_flag=flag,
                )
            )
        bias_corrected = bias_flag[key]
        metadata = TimeseriesMetadata(
            source="ensemble",
            source_url=None,
            units=base_point.metadata.units,
            bias_corrected=bias_corrected,
            ensemble_weight=1.0,
        )
        ensemble_points.append(
            MarineDataPoint(
                timestamp=base_point.timestamp,
                position=base_point.position,
                measurements=aggregated_measurements,
                metadata=metadata,
            )
        )
    return MarineTimeseries(points=ensemble_points)
