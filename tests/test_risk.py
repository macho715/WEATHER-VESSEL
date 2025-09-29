from datetime import datetime, timezone

import pytest

from wv.core.models import ForecastPoint
from wv.core.risk import RiskAssessment, RiskLevel, compute_risk
from wv.core.utils import format_metric


def test_format_metric_two_decimals():
    assert format_metric(1.234) == "1.23"
    assert format_metric(5) == "5.00"


@pytest.mark.parametrize(
    "hs,wind,risk_level",
    [
        (1.99, 21.9, RiskLevel.LOW),
        (2.01, 10.0, RiskLevel.MEDIUM),
        (0.5, 28.5, RiskLevel.HIGH),
        (3.5, 15.0, RiskLevel.HIGH),
    ],
)
def test_compute_risk_thresholds(hs: float, wind: float, risk_level: RiskLevel) -> None:
    point = ForecastPoint(
        time=datetime.now(timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=hs,
        tp=10.0,
        dp=180.0,
        wind_speed=wind,
        wind_dir=90.0,
        swell_height=hs,
        swell_period=11.0,
        swell_direction=200.0,
    )
    assessment = compute_risk(point)
    assert assessment.level is risk_level


def test_compute_risk_missing_swell_is_conservative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WV_MEDIUM_HS", "2.0")
    monkeypatch.setenv("WV_HIGH_HS", "3.0")
    point = ForecastPoint(
        time=datetime.now(timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=1.5,
        tp=None,
        dp=None,
        wind_speed=10.0,
        wind_dir=45.0,
        swell_height=None,
        swell_period=None,
        swell_direction=None,
    )
    assessment = compute_risk(point)
    assert assessment.level is RiskLevel.MEDIUM
    assert "Missing swell" in assessment.reasons[0]


def test_risk_assessment_metrics_are_formatted() -> None:
    point = ForecastPoint(
        time=datetime.now(timezone.utc),
        lat=24.3,
        lon=54.4,
        hs=1.234,
        tp=9.876,
        dp=200.0,
        wind_speed=15.4321,
        wind_dir=120.0,
        swell_height=1.0,
        swell_period=14.0,
        swell_direction=220.0,
    )
    assessment = compute_risk(point)
    for value in assessment.metrics.values():
        before, _, after = value.partition(" ")
        assert "." in before
        whole, _, decimal = before.partition(".")
        assert len(decimal) == 2
        assert len(whole) >= 1
        assert len(after) > 0


def test_risk_assessment_serialization_round_trip() -> None:
    now = datetime.now(timezone.utc)
    point = ForecastPoint(
        time=now,
        lat=24.3,
        lon=54.4,
        hs=1.0,
        tp=8.0,
        dp=180.0,
        wind_speed=12.0,
        wind_dir=45.0,
        swell_height=0.8,
        swell_period=12.0,
        swell_direction=200.0,
    )
    assessment = compute_risk(point)
    serialized = assessment.model_dump()
    restored = RiskAssessment.model_validate(serialized)
    assert restored == assessment
