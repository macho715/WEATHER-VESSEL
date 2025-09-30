"""ERI 규칙 및 통합 테스트. ERI rules and integration tests."""

from __future__ import annotations

import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

from marine_ops.core.bias import apply_bias_correction
from marine_ops.core.qc import apply_quality_controls
from marine_ops.core.schema import (
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    Position,
    QualityFlag,
    TimeseriesMetadata,
    UnitEnum,
)
from marine_ops.eri.compute import compute_eri_timeseries
from marine_ops.eri.rules import load_rule_set

FIXTURE_DIR = Path(__file__).parent / "fixtures"
ROOT_DIR = Path(__file__).resolve().parents[2]


def parse_sample_timeseries(path: Path) -> MarineTimeseries:
    """샘플 CSV 파싱. Parse sample CSV."""

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            groups[row["timestamp"]].append(row)
    points: list[MarineDataPoint] = []
    for timestamp_str, rows in groups.items():
        timestamp = dt.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc
        )
        latitude = float(rows[0]["latitude"])
        longitude = float(rows[0]["longitude"])
        unit_map = {MarineVariable(row["variable"]): UnitEnum(row["unit"]) for row in rows}
        metadata = TimeseriesMetadata(
            source=rows[0]["source"],
            source_url=None,
            units=unit_map,
            bias_corrected=rows[0]["bias_corrected"].lower() == "true",
        )
        measurements: list[MarineMeasurement] = []
        for row in rows:
            variable = MarineVariable(row["variable"])
            unit = UnitEnum(row["unit"])
            flag = QualityFlag(row["quality_flag"])
            measurements.append(
                MarineMeasurement(
                    variable=variable,
                    value=float(row["value"]),
                    unit=unit,
                    quality_flag=flag,
                )
            )
        points.append(
            MarineDataPoint(
                timestamp=timestamp,
                position=Position(latitude=latitude, longitude=longitude),
                measurements=measurements,
                metadata=metadata,
            )
        )
    return MarineTimeseries(points=sorted(points, key=lambda item: item.timestamp))


def test_eri_computation_from_sample_csv(tmp_path: Path) -> None:
    rules = load_rule_set(FIXTURE_DIR / "eri_rules.yaml")
    sample_csv = ROOT_DIR / "sample_timeseries.csv"
    timeseries = parse_sample_timeseries(sample_csv)
    qc_series = apply_quality_controls(
        timeseries, {MarineVariable.SIGNIFICANT_WAVE_HEIGHT: (0.0, 4.0)}
    )
    background = {MarineVariable.SIGNIFICANT_WAVE_HEIGHT: [1.0, 1.1, 1.2]}
    corrected = apply_bias_correction(qc_series, background, enabled=True)
    eri_points = compute_eri_timeseries(corrected, rules)
    assert len(eri_points) == len(corrected.points)
    assert all(0 <= point.score <= 100 for point in eri_points)
    assert any(point.quality.bias_corrected for point in eri_points)
