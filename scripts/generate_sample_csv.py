"""샘플 CSV 생성 스크립트. Sample CSV generation script."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

from marine_ops import (
    CSV_HEADER,
    CSV_TIMESTAMP_FORMAT,
    MarineDataPoint,
    MarineMeasurement,
    MarineTimeseries,
    MarineVariable,
    Position,
    TimeseriesMetadata,
    UnitEnum,
)

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent


def build_sample_timeseries() -> MarineTimeseries:
    """데모용 해양 시계열 구성. Build demo marine timeseries."""

    base_time = dt.datetime(2025, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
    metadata = TimeseriesMetadata(
        source="sample",
        source_url=None,
        units={
            MarineVariable.SIGNIFICANT_WAVE_HEIGHT: UnitEnum.METERS,
            MarineVariable.WIND_SPEED_10M: UnitEnum.METERS_PER_SECOND,
            MarineVariable.WIND_DIRECTION_10M: UnitEnum.DEGREES,
            MarineVariable.VISIBILITY: UnitEnum.KILOMETERS,
        },
    )
    points: list[MarineDataPoint] = []
    for hour in range(6):
        timestamp = base_time + dt.timedelta(hours=hour)
        measurements = [
            MarineMeasurement(
                variable=MarineVariable.SIGNIFICANT_WAVE_HEIGHT,
                value=1.2 + 0.1 * hour,
                unit=UnitEnum.METERS,
            ),
            MarineMeasurement(
                variable=MarineVariable.WIND_SPEED_10M,
                value=8.0 + hour,
                unit=UnitEnum.METERS_PER_SECOND,
            ),
            MarineMeasurement(
                variable=MarineVariable.WIND_DIRECTION_10M,
                value=180.0,
                unit=UnitEnum.DEGREES,
            ),
            MarineMeasurement(
                variable=MarineVariable.VISIBILITY,
                value=15.0,
                unit=UnitEnum.KILOMETERS,
            ),
        ]
        points.append(
            MarineDataPoint(
                timestamp=timestamp,
                position=Position(latitude=25.0, longitude=55.0),
                measurements=measurements,
                metadata=metadata,
            )
        )
    return MarineTimeseries(points=points)


def write_timeseries_csv(timeseries: MarineTimeseries, path: Path) -> None:
    """시계열 CSV 저장. Save timeseries CSV."""

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        for row in timeseries.iter_rows():
            writer.writerow(row)


def write_jobs_csv(path: Path) -> None:
    """작업 샘플 CSV 저장. Save jobs sample CSV."""

    header = ("job_id", "latitude", "longitude", "start", "end")
    base_time = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    rows = [
        (
            "demo-001",
            "25.00",
            "55.00",
            base_time.strftime(CSV_TIMESTAMP_FORMAT),
            (base_time + dt.timedelta(hours=24)).strftime(CSV_TIMESTAMP_FORMAT),
        ),
        (
            "demo-002",
            "24.50",
            "54.80",
            (base_time + dt.timedelta(hours=12)).strftime(CSV_TIMESTAMP_FORMAT),
            (base_time + dt.timedelta(hours=36)).strftime(CSV_TIMESTAMP_FORMAT),
        ),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    """샘플 CSV 생성 실행. Execute sample CSV generation."""

    parser = argparse.ArgumentParser(description="Generate sample marine operations CSV files")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Target directory for CSV files"
    )
    args = parser.parse_args()
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    timeseries_path = output_dir / "sample_timeseries.csv"
    jobs_path = output_dir / "sample_jobs.csv"
    write_timeseries_csv(build_sample_timeseries(), timeseries_path)
    write_jobs_csv(jobs_path)
    print(f"Generated {timeseries_path}")
    print(f"Generated {jobs_path}")


if __name__ == "__main__":
    main()
