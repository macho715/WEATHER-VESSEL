"""코어 유틸리티 테스트. Core utility tests."""

from __future__ import annotations

import datetime as dt

import httpx
import pytest

from marine_ops.core import MarineOpsSettings, bias, ensemble, qc
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
from marine_ops.core.units import (
    feet_to_meters,
    knots_to_meters_per_second,
    meters_per_second_to_knots,
)


def make_point(
    value: float,
    timestamp: dt.datetime | None = None,
    source: str = "stormglass",
) -> MarineDataPoint:
    timestamp = timestamp or dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
    metadata = TimeseriesMetadata(
        source=source,
        source_url=None,
        units={MarineVariable.SIGNIFICANT_WAVE_HEIGHT: UnitEnum.METERS},
    )
    measurement = MarineMeasurement(
        variable=MarineVariable.SIGNIFICANT_WAVE_HEIGHT,
        value=value,
        unit=UnitEnum.METERS,
    )
    return MarineDataPoint(
        timestamp=timestamp,
        position=Position(latitude=25.0, longitude=55.0),
        measurements=[measurement],
        metadata=metadata,
    )


def test_unit_conversions_round_trip() -> None:
    speed_ms = knots_to_meters_per_second(10)
    assert speed_ms == 5.14
    assert abs(meters_per_second_to_knots(speed_ms) - 10.0) <= 0.02
    assert feet_to_meters(10) == 3.05


def test_quality_control_clips_outliers() -> None:
    raw_series = MarineTimeseries(
        points=[
            make_point(0.5),
            make_point(5.0, dt.datetime(2025, 1, 1, 1, tzinfo=dt.timezone.utc)),
        ]
    )
    cleaned = qc.apply_quality_controls(
        raw_series,
        physical_bounds={MarineVariable.SIGNIFICANT_WAVE_HEIGHT: (0.0, 4.0)},
    )
    assert cleaned.points[1].measurements[0].value == 4.0
    assert cleaned.points[1].measurements[0].quality_flag == QualityFlag.CLIPPED


def test_bias_correction_adjusts_mean() -> None:
    series = MarineTimeseries(points=[make_point(1.0), make_point(1.5)])
    background = {MarineVariable.SIGNIFICANT_WAVE_HEIGHT: [0.8, 0.9, 1.0]}
    corrected = bias.apply_bias_correction(series, background)
    values = [point.measurements[0].value for point in corrected.points]
    assert corrected.points[0].metadata.bias_corrected is True
    assert round(sum(values) / len(values), 2) == 0.9


def test_weighted_ensemble_combines_series() -> None:
    point_a = make_point(1.0, source="stormglass")
    point_b = make_point(2.0, source="open-meteo")
    series_a = MarineTimeseries(points=[point_a])
    series_b = MarineTimeseries(points=[point_b])
    blended = ensemble.weighted_ensemble(
        [series_a, series_b], {"stormglass": 0.7, "open-meteo": 0.3}
    )
    assert len(blended.points) == 1
    assert blended.points[0].measurements[0].value == 1.3


def test_settings_from_env_parses_timeout() -> None:
    env = {
        "STORMGLASS_API_KEY": "storm",
        "WORLDTIDES_API_KEY": "tide",
        "OPEN_METEO_BASE": "https://example.com/api",
        "OPEN_METEO_TIMEOUT": "12.75",
        "APP_LOG_LEVEL": "DEBUG",
    }
    settings = MarineOpsSettings.from_env(env)
    assert settings.stormglass_api_key == "storm"
    assert settings.worldtides_api_key == "tide"
    assert settings.open_meteo_base == "https://example.com/api"
    assert settings.open_meteo_timeout == 12.75
    assert settings.app_log_level == "DEBUG"


def test_settings_builders_require_keys() -> None:
    settings = MarineOpsSettings.from_env({})
    with pytest.raises(ValueError):
        settings.build_stormglass_connector()
    with pytest.raises(ValueError):
        settings.build_worldtides_connector()


def test_settings_builders_use_env_base() -> None:
    env = {
        "STORMGLASS_API_KEY": "storm",
        "WORLDTIDES_API_KEY": "tide",
        "OPEN_METEO_BASE": "https://alt.example/marine",
    }
    settings = MarineOpsSettings.from_env(env)
    fallback = settings.build_open_meteo_fallback(
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    )
    try:
        assert fallback.base_url == "https://alt.example/marine"
    finally:
        fallback.client.close()
